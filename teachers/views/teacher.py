import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from teachers.models import Teacher
from teachers.serializers.teacher import (
    TeacherMinimalSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    TeacherDisplaySerializer,
)
from teachers.services.teacher import TeacherService

logger = logging.getLogger(__name__)

def can_view_teacher(user, teacher):
    if user.is_staff:
        return True
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        return teacher == user.teacher_profile
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        # Students can see their teachers via assignments
        return teacher.assignments.filter(section__enrollments__student=user.student_profile).exists()
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        # Parents can see teachers of their children
        child_ids = user.parent_profile.students.values_list('student_id', flat=True)
        return teacher.assignments.filter(section__enrollments__student_id__in=child_ids).exists()
    return False

def can_manage_teacher(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TeacherCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    teacher_id = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()

class TeacherCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherCreateResponseData(allow_null=True)

class TeacherUpdateResponseData(serializers.Serializer):
    teacher = TeacherDisplaySerializer()

class TeacherUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherUpdateResponseData(allow_null=True)

class TeacherDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TeacherDetailResponseData(serializers.Serializer):
    teacher = TeacherDisplaySerializer()

class TeacherDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherDetailResponseData(allow_null=True)

class TeacherListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TeacherMinimalSerializer(many=True)

class TeacherListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherListResponseData()

def wrap_paginated_data(paginator, page, request, serializer_class):
    serializer = serializer_class(page, many=True, context={'request': request})
    return {
        'page': paginator.page.number,
        'hasNext': paginator.page.has_next(),
        'hasPrev': paginator.page.has_previous(),
        'count': paginator.page.paginator.count,
        'next': paginator.get_next_link(),
        'previous': paginator.get_previous_link(),
        'results': serializer.data,
    }

# ----------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------

class TeacherListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Teachers"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="department_id", type=int, description="Filter by department (via employee)", required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: TeacherListResponseSerializer},
        description="List teachers (filtered by role)."
    )
    def get(self, request):
        user = request.user
        department_id = request.query_params.get("department_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        if user.is_staff or can_manage_teacher(user):
            queryset = Teacher.objects.all()
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                # Get teachers from student's enrollments
                from enrollments.models import Enrollment
                enrollments = Enrollment.objects.filter(student=user.student_profile, status='ENR')
                section_ids = enrollments.values_list('section_id', flat=True)
                from teachers.models import TeachingAssignment
                teacher_ids = TeachingAssignment.objects.filter(section_id__in=section_ids, is_active=True).values_list('teacher_id', flat=True)
                queryset = Teacher.objects.filter(id__in=teacher_ids)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                from enrollments.models import Enrollment
                enrollments = Enrollment.objects.filter(student_id__in=child_ids, status='ENR')
                section_ids = enrollments.values_list('section_id', flat=True)
                from teachers.models import TeachingAssignment
                teacher_ids = TeachingAssignment.objects.filter(section_id__in=section_ids, is_active=True).values_list('teacher_id', flat=True)
                queryset = Teacher.objects.filter(id__in=teacher_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if department_id:
            # Department filter via employee (HR app)
            from hr.models import Employee
            teacher_user_ids = Employee.objects.filter(department_id=department_id).values_list('user_id', flat=True)
            queryset = queryset.filter(user_id__in=teacher_user_ids)
        if active_only:
            queryset = queryset.filter(status='ACT')

        queryset = queryset.order_by('last_name', 'first_name')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, TeacherMinimalSerializer)
        return Response({
            "status": True,
            "message": "Teachers retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Teachers"],
        request=TeacherCreateSerializer,
        responses={201: TeacherCreateResponseSerializer, 400: TeacherCreateResponseSerializer, 403: TeacherCreateResponseSerializer},
        description="Create a new teacher (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_teacher(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = TeacherCreateSerializer(data=request.data)
        if serializer.is_valid():
            teacher = serializer.save()
            return Response({
                "status": True,
                "message": "Teacher created.",
                "data": {
                    "id": teacher.id,
                    "teacher_id": teacher.teacher_id,
                    "first_name": teacher.first_name,
                    "last_name": teacher.last_name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeacherDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, teacher_id):
        try:
            return Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return None

    @extend_schema(
        tags=["Teachers"],
        responses={200: TeacherDetailResponseSerializer, 404: TeacherDetailResponseSerializer, 403: TeacherDetailResponseSerializer},
        description="Retrieve a single teacher by ID."
    )
    def get(self, request, teacher_id):
        teacher = self.get_object(teacher_id)
        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_teacher(request.user, teacher):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = TeacherDisplaySerializer(teacher, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Teacher retrieved.",
            "data": {"teacher": data}
        })

    @extend_schema(
        tags=["Teachers"],
        request=TeacherUpdateSerializer,
        responses={200: TeacherUpdateResponseSerializer, 400: TeacherUpdateResponseSerializer, 403: TeacherUpdateResponseSerializer},
        description="Update a teacher (admin/hr only)."
    )
    @transaction.atomic
    def put(self, request, teacher_id):
        return self._update(request, teacher_id, partial=False)

    @extend_schema(
        tags=["Teachers"],
        request=TeacherUpdateSerializer,
        responses={200: TeacherUpdateResponseSerializer, 400: TeacherUpdateResponseSerializer, 403: TeacherUpdateResponseSerializer},
        description="Partially update a teacher."
    )
    @transaction.atomic
    def patch(self, request, teacher_id):
        return self._update(request, teacher_id, partial=True)

    def _update(self, request, teacher_id, partial):
        if not can_manage_teacher(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        teacher = self.get_object(teacher_id)
        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TeacherUpdateSerializer(teacher, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = TeacherDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Teacher updated.",
                "data": {"teacher": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Teachers"],
        responses={200: TeacherDeleteResponseSerializer, 403: TeacherDeleteResponseSerializer, 404: TeacherDeleteResponseSerializer},
        description="Delete a teacher (admin only)."
    )
    @transaction.atomic
    def delete(self, request, teacher_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        teacher = self.get_object(teacher_id)
        if not teacher:
            return Response({
                "status": False,
                "message": "Teacher not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = TeacherService.delete_teacher(teacher)
        if success:
            return Response({
                "status": True,
                "message": "Teacher deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete teacher.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Teachers"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: TeacherListResponseSerializer},
        description="Search teachers by name, ID, or email (admin/hr only)."
    )
    def get(self, request):
        if not can_manage_teacher(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        teachers = TeacherService.search_teachers(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(teachers, request)
        data = wrap_paginated_data(paginator, page, request, TeacherMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })