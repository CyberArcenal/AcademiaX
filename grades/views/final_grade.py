import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from grades.models import FinalGrade
from grades.serializers.final_grade import (
    FinalGradeMinimalSerializer,
    FinalGradeCreateSerializer,
    FinalGradeUpdateSerializer,
    FinalGradeDisplaySerializer,
)
from grades.services.final_grade import FinalGradeService

logger = logging.getLogger(__name__)

def can_view_final_grade(user, final_grade):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return final_grade.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return final_grade.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        # Teacher can see final grades for subjects they teach
        return final_grade.subject.teacher_assignments.filter(teacher=user.teacher_profile, is_active=True).exists()
    return False

def can_manage_final_grade(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'TEACHER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class FinalGradeCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    subject = serializers.IntegerField()
    final_grade = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

class FinalGradeCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FinalGradeCreateResponseData(allow_null=True)

class FinalGradeUpdateResponseData(serializers.Serializer):
    final_grade = FinalGradeDisplaySerializer()

class FinalGradeUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FinalGradeUpdateResponseData(allow_null=True)

class FinalGradeDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class FinalGradeDetailResponseData(serializers.Serializer):
    final_grade = FinalGradeDisplaySerializer()

class FinalGradeDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FinalGradeDetailResponseData(allow_null=True)

class FinalGradeListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = FinalGradeMinimalSerializer(many=True)

class FinalGradeListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FinalGradeListResponseData()

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

class FinalGradeListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Final Grades"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject ID", required=False),
            OpenApiParameter(name="enrollment_id", type=int, description="Filter by enrollment ID", required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year ID", required=False),
        ],
        responses={200: FinalGradeListResponseSerializer},
        description="List final grades (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        subject_id = request.query_params.get("subject_id")
        enrollment_id = request.query_params.get("enrollment_id")
        academic_year_id = request.query_params.get("academic_year_id")

        if user.is_staff or can_manage_final_grade(user):
            queryset = FinalGrade.objects.all().select_related('student', 'subject', 'enrollment', 'academic_year')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = FinalGrade.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = FinalGrade.objects.filter(student_id__in=child_ids)
            elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                # Teacher sees final grades for subjects they teach
                teacher = user.teacher_profile
                subject_ids = teacher.specializations.values_list('subject_id', flat=True)
                queryset = FinalGrade.objects.filter(subject_id__in=subject_ids)
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
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, FinalGradeMinimalSerializer)
        return Response({
            "status": True,
            "message": "Final grades retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Grades - Final Grades"],
        request=FinalGradeCreateSerializer,
        responses={201: FinalGradeCreateResponseSerializer, 400: FinalGradeCreateResponseSerializer, 403: FinalGradeCreateResponseSerializer},
        description="Create a final grade (teacher/admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_final_grade(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = FinalGradeCreateSerializer(data=request.data)
        if serializer.is_valid():
            final_grade = serializer.save()
            return Response({
                "status": True,
                "message": "Final grade created.",
                "data": {
                    "id": final_grade.id,
                    "student": final_grade.student.id,
                    "subject": final_grade.subject.id,
                    "final_grade": final_grade.final_grade,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FinalGradeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, final_id):
        try:
            return FinalGrade.objects.select_related('student', 'subject', 'enrollment', 'academic_year').get(id=final_id)
        except FinalGrade.DoesNotExist:
            return None

    @extend_schema(
        tags=["Grades - Final Grades"],
        responses={200: FinalGradeDetailResponseSerializer, 404: FinalGradeDetailResponseSerializer, 403: FinalGradeDetailResponseSerializer},
        description="Retrieve a single final grade by ID."
    )
    def get(self, request, final_id):
        final_grade = self.get_object(final_id)
        if not final_grade:
            return Response({
                "status": False,
                "message": "Final grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_final_grade(request.user, final_grade):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = FinalGradeDisplaySerializer(final_grade, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Final grade retrieved.",
            "data": {"final_grade": data}
        })

    @extend_schema(
        tags=["Grades - Final Grades"],
        request=FinalGradeUpdateSerializer,
        responses={200: FinalGradeUpdateResponseSerializer, 400: FinalGradeUpdateResponseSerializer, 403: FinalGradeUpdateResponseSerializer},
        description="Update a final grade (teacher/admin only)."
    )
    @transaction.atomic
    def put(self, request, final_id):
        return self._update(request, final_id, partial=False)

    @extend_schema(
        tags=["Grades - Final Grades"],
        request=FinalGradeUpdateSerializer,
        responses={200: FinalGradeUpdateResponseSerializer, 400: FinalGradeUpdateResponseSerializer, 403: FinalGradeUpdateResponseSerializer},
        description="Partially update a final grade."
    )
    @transaction.atomic
    def patch(self, request, final_id):
        return self._update(request, final_id, partial=True)

    def _update(self, request, final_id, partial):
        if not can_manage_final_grade(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        final_grade = self.get_object(final_id)
        if not final_grade:
            return Response({
                "status": False,
                "message": "Final grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = FinalGradeUpdateSerializer(final_grade, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = FinalGradeDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Final grade updated.",
                "data": {"final_grade": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Grades - Final Grades"],
        responses={200: FinalGradeDeleteResponseSerializer, 403: FinalGradeDeleteResponseSerializer, 404: FinalGradeDeleteResponseSerializer},
        description="Delete a final grade (admin only)."
    )
    @transaction.atomic
    def delete(self, request, final_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        final_grade = self.get_object(final_id)
        if not final_grade:
            return Response({
                "status": False,
                "message": "Final grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = FinalGradeService.delete_final_grade(final_grade)
        if success:
            return Response({
                "status": True,
                "message": "Final grade deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete final grade.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinalGradeComputeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Final Grades"],
        responses={200: FinalGradeUpdateResponseSerializer, 403: FinalGradeUpdateResponseSerializer, 404: FinalGradeUpdateResponseSerializer},
        description="Compute final grade from quarterly grades (teacher/admin only)."
    )
    @transaction.atomic
    def post(self, request, final_id):
        if not can_manage_final_grade(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        final_grade = FinalGradeService.get_final_grade_by_id(final_id)
        if not final_grade:
            return Response({
                "status": False,
                "message": "Final grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        computed = FinalGradeService.compute_final_grade(final_grade)
        data = FinalGradeDisplaySerializer(computed, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Final grade computed.",
            "data": {"final_grade": data}
        })