import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from grades.models import Grade
from grades.serializers.grade import (
    GradeMinimalSerializer,
    GradeCreateSerializer,
    GradeUpdateSerializer,
    GradeDisplaySerializer,
)
from grades.services.grade import GradeService
from enrollments.services.enrollment import EnrollmentService

logger = logging.getLogger(__name__)

def can_view_grade(user, grade):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return grade.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return grade.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        return grade.teacher == user.teacher_profile
    return False

def can_manage_grade(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'TEACHER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class GradeCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    subject = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)

class GradeCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeCreateResponseData(allow_null=True)

class GradeUpdateResponseData(serializers.Serializer):
    grade = GradeDisplaySerializer()

class GradeUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeUpdateResponseData(allow_null=True)

class GradeDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class GradeDetailResponseData(serializers.Serializer):
    grade = GradeDisplaySerializer()

class GradeDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeDetailResponseData(allow_null=True)

class GradeListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = GradeMinimalSerializer(many=True)

class GradeListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeListResponseData()

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

class GradeListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject ID", required=False),
            OpenApiParameter(name="enrollment_id", type=int, description="Filter by enrollment ID", required=False),
            OpenApiParameter(name="term_id", type=int, description="Filter by term ID", required=False),
        ],
        responses={200: GradeListResponseSerializer},
        description="List grades (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        subject_id = request.query_params.get("subject_id")
        enrollment_id = request.query_params.get("enrollment_id")
        term_id = request.query_params.get("term_id")

        if user.is_staff or can_manage_grade(user):
            queryset = Grade.objects.all().select_related('student', 'subject', 'enrollment', 'teacher', 'term', 'graded_by')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = Grade.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = Grade.objects.filter(student_id__in=child_ids)
            elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                queryset = Grade.objects.filter(teacher=user.teacher_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if enrollment_id:
            queryset = queryset.filter(enrollment_id=enrollment_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, GradeMinimalSerializer)
        return Response({
            "status": True,
            "message": "Grades retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Grades"],
        request=GradeCreateSerializer,
        responses={201: GradeCreateResponseSerializer, 400: GradeCreateResponseSerializer, 403: GradeCreateResponseSerializer},
        description="Create a grade (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_grade(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = GradeCreateSerializer(data=request.data)
        if serializer.is_valid():
            grade = serializer.save()
            return Response({
                "status": True,
                "message": "Grade created.",
                "data": {
                    "id": grade.id,
                    "student": grade.student.id,
                    "subject": grade.subject.id,
                    "percentage": grade.percentage,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GradeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, grade_id):
        try:
            return Grade.objects.select_related('student', 'subject', 'enrollment', 'teacher', 'term', 'graded_by').get(id=grade_id)
        except Grade.DoesNotExist:
            return None

    @extend_schema(
        tags=["Grades"],
        responses={200: GradeDetailResponseSerializer, 404: GradeDetailResponseSerializer, 403: GradeDetailResponseSerializer},
        description="Retrieve a single grade by ID."
    )
    def get(self, request, grade_id):
        grade = self.get_object(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_grade(request.user, grade):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = GradeDisplaySerializer(grade, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Grade retrieved.",
            "data": {"grade": data}
        })

    @extend_schema(
        tags=["Grades"],
        request=GradeUpdateSerializer,
        responses={200: GradeUpdateResponseSerializer, 400: GradeUpdateResponseSerializer, 403: GradeUpdateResponseSerializer},
        description="Update a grade (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, grade_id):
        return self._update(request, grade_id, partial=False)

    @extend_schema(
        tags=["Grades"],
        request=GradeUpdateSerializer,
        responses={200: GradeUpdateResponseSerializer, 400: GradeUpdateResponseSerializer, 403: GradeUpdateResponseSerializer},
        description="Partially update a grade."
    )
    @transaction.atomic
    def patch(self, request, grade_id):
        return self._update(request, grade_id, partial=True)

    def _update(self, request, grade_id, partial):
        if not can_manage_grade(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        grade = self.get_object(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = GradeUpdateSerializer(grade, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = GradeDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Grade updated.",
                "data": {"grade": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Grades"],
        responses={200: GradeDeleteResponseSerializer, 403: GradeDeleteResponseSerializer, 404: GradeDeleteResponseSerializer},
        description="Delete a grade (admin only)."
    )
    @transaction.atomic
    def delete(self, request, grade_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        grade = self.get_object(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = GradeService.delete_grade(grade)
        if success:
            return Response({
                "status": True,
                "message": "Grade deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete grade.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GradeSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades"],
        responses={200: GradeUpdateResponseSerializer, 403: GradeUpdateResponseSerializer, 404: GradeUpdateResponseSerializer},
        description="Submit a grade (teacher, for approval)."
    )
    @transaction.atomic
    def post(self, request, grade_id):
        if not can_manage_grade(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        grade = GradeService.get_grade_by_id(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if grade.status != 'DRF':
            return Response({
                "status": False,
                "message": "Only draft grades can be submitted.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = GradeService.submit_grade(grade)
        data = GradeDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Grade submitted for approval.",
            "data": {"grade": data}
        })


class GradeApproveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades"],
        responses={200: GradeUpdateResponseSerializer, 403: GradeUpdateResponseSerializer, 404: GradeUpdateResponseSerializer},
        description="Approve a grade (admin only)."
    )
    @transaction.atomic
    def post(self, request, grade_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        grade = GradeService.get_grade_by_id(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if grade.status != 'SUB':
            return Response({
                "status": False,
                "message": "Only submitted grades can be approved.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = GradeService.approve_grade(grade)
        data = GradeDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Grade approved.",
            "data": {"grade": data}
        })