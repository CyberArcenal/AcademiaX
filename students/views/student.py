import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from students.models import Student
from students.serializers.student import (
    StudentMinimalSerializer,
    StudentCreateSerializer,
    StudentUpdateSerializer,
    StudentDisplaySerializer,
)
from students.services.student import StudentService

logger = logging.getLogger(__name__)

def can_view_student(user, student):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        # Parent can see their children
        return student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        # Teacher can see students in sections they teach
        teacher = user.teacher_profile
        sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
        from enrollments.models import Enrollment
        student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
        return student.id in student_ids
    return False

def can_manage_student(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class StudentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student_id = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()

class StudentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentCreateResponseData(allow_null=True)

class StudentUpdateResponseData(serializers.Serializer):
    student = StudentDisplaySerializer()

class StudentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentUpdateResponseData(allow_null=True)

class StudentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class StudentDetailResponseData(serializers.Serializer):
    student = StudentDisplaySerializer()

class StudentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentDetailResponseData(allow_null=True)

class StudentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = StudentMinimalSerializer(many=True)

class StudentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentListResponseData()

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

class StudentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Students"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="grade_level_id", type=int, description="Filter by grade level (via enrollment)", required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active students", required=False),
        ],
        responses={200: StudentListResponseSerializer},
        description="List students (filtered by role)."
    )
    def get(self, request):
        user = request.user
        grade_level_id = request.query_params.get("grade_level_id")
        academic_year_id = request.query_params.get("academic_year_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        if user.is_staff or can_manage_student(user):
            queryset = Student.objects.all()
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = Student.objects.filter(id=user.student_profile.id)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = Student.objects.filter(id__in=child_ids)
            elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                teacher = user.teacher_profile
                sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                from enrollments.models import Enrollment
                student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
                queryset = Student.objects.filter(id__in=student_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if active_only:
            queryset = queryset.filter(status='ACT')

        # Filter by grade level and academic year using enrollments
        if grade_level_id or academic_year_id:
            from enrollments.models import Enrollment
            enrollment_filter = {}
            if grade_level_id:
                enrollment_filter['grade_level_id'] = grade_level_id
            if academic_year_id:
                enrollment_filter['academic_year_id'] = academic_year_id
            student_ids = Enrollment.objects.filter(**enrollment_filter, status='ENR').values_list('student_id', flat=True)
            queryset = queryset.filter(id__in=student_ids)

        queryset = queryset.order_by('last_name', 'first_name')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, StudentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Students retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Students"],
        request=StudentCreateSerializer,
        responses={201: StudentCreateResponseSerializer, 400: StudentCreateResponseSerializer, 403: StudentCreateResponseSerializer},
        description="Create a new student (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_student(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = StudentCreateSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            return Response({
                "status": True,
                "message": "Student created.",
                "data": {
                    "id": student.id,
                    "student_id": student.student_id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, student_id):
        try:
            return Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return None

    @extend_schema(
        tags=["Students"],
        responses={200: StudentDetailResponseSerializer, 404: StudentDetailResponseSerializer, 403: StudentDetailResponseSerializer},
        description="Retrieve a single student by ID."
    )
    def get(self, request, student_id):
        student = self.get_object(student_id)
        if not student:
            return Response({
                "status": False,
                "message": "Student not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_student(request.user, student):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = StudentDisplaySerializer(student, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Student retrieved.",
            "data": {"student": data}
        })

    @extend_schema(
        tags=["Students"],
        request=StudentUpdateSerializer,
        responses={200: StudentUpdateResponseSerializer, 400: StudentUpdateResponseSerializer, 403: StudentUpdateResponseSerializer},
        description="Update a student (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, student_id):
        return self._update(request, student_id, partial=False)

    @extend_schema(
        tags=["Students"],
        request=StudentUpdateSerializer,
        responses={200: StudentUpdateResponseSerializer, 400: StudentUpdateResponseSerializer, 403: StudentUpdateResponseSerializer},
        description="Partially update a student."
    )
    @transaction.atomic
    def patch(self, request, student_id):
        return self._update(request, student_id, partial=True)

    def _update(self, request, student_id, partial):
        if not can_manage_student(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        student = self.get_object(student_id)
        if not student:
            return Response({
                "status": False,
                "message": "Student not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentUpdateSerializer(student, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = StudentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Student updated.",
                "data": {"student": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Students"],
        responses={200: StudentDeleteResponseSerializer, 403: StudentDeleteResponseSerializer, 404: StudentDeleteResponseSerializer},
        description="Delete a student (soft delete, admin only)."
    )
    @transaction.atomic
    def delete(self, request, student_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        student = self.get_object(student_id)
        if not student:
            return Response({
                "status": False,
                "message": "Student not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = StudentService.delete_student(student)
        if success:
            return Response({
                "status": True,
                "message": "Student deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete student.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Students"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: StudentListResponseSerializer},
        description="Search students by name, ID, or LRN (admin/registrar only)."
    )
    def get(self, request):
        if not can_manage_student(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        students = StudentService.search_students(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(students, request)
        data = wrap_paginated_data(paginator, page, request, StudentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })