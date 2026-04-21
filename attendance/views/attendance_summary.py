import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from attendance.models import StudentAttendanceSummary
from attendance.serializers.attendance_summary import (
    StudentAttendanceSummaryMinimalSerializer,
    StudentAttendanceSummaryCreateSerializer,
    StudentAttendanceSummaryUpdateSerializer,
    StudentAttendanceSummaryDisplaySerializer,
)
from attendance.services.attendance_summary import StudentAttendanceSummaryService
from common.base.paginations import StandardResultsSetPagination


logger = logging.getLogger(__name__)

# Helper to check if user can view summary for a student
def can_view_summary(user, summary):
    if user.is_staff:
        return True
    if user.role == 'TEACHER':
        from classes.models import Section
        teacher = user.teacher_profile
        assigned_section_ids = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
        student_sections = summary.student.enrollments.filter(section_id__in=assigned_section_ids, status='ENR').exists()
        return student_sections
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return summary.student == user.student_profile
    return False

def can_manage_summary(user):
    return user.is_authenticated and (user.role == 'TEACHER' or user.is_staff)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class SummaryCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    term = serializers.CharField()

class SummaryCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SummaryCreateResponseData(allow_null=True)

class SummaryUpdateResponseData(serializers.Serializer):
    summary = StudentAttendanceSummaryDisplaySerializer()

class SummaryUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SummaryUpdateResponseData(allow_null=True)

class SummaryDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class SummaryDetailResponseData(serializers.Serializer):
    summary = StudentAttendanceSummaryDisplaySerializer()

class SummaryDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SummaryDetailResponseData(allow_null=True)

class SummaryListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = StudentAttendanceSummaryMinimalSerializer(many=True)

class SummaryListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SummaryListResponseData()

class SummaryRecalculateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SummaryDetailResponseData()

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

class StudentAttendanceSummaryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Attendance - Summary"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year", required=False),
        ],
        responses={200: SummaryListResponseSerializer},
        description="List student attendance summaries (teachers see their students, admins see all)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        academic_year_id = request.query_params.get("academic_year_id")
        queryset = StudentAttendanceSummary.objects.all().select_related('student', 'academic_year')
        if not user.is_staff:
            if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                teacher = user.teacher_profile
                assigned_section_ids = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                from enrollments.models import Enrollment
                student_ids = Enrollment.objects.filter(section_id__in=assigned_section_ids, status='ENR').values_list('student_id', flat=True)
                queryset = queryset.filter(student_id__in=student_ids)
            elif user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = queryset.filter(student=user.student_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, StudentAttendanceSummaryMinimalSerializer)
        return Response({
            "status": True,
            "message": "Attendance summaries retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Attendance - Summary"],
        request=StudentAttendanceSummaryCreateSerializer,
        responses={201: SummaryCreateResponseSerializer, 400: SummaryCreateResponseSerializer, 403: SummaryCreateResponseSerializer},
        description="Create an attendance summary (usually auto-generated, but available for manual creation)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_summary(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = StudentAttendanceSummaryCreateSerializer(data=request.data)
        if serializer.is_valid():
            summary = serializer.save()
            return Response({
                "status": True,
                "message": "Attendance summary created.",
                "data": {
                    "id": summary.id,
                    "student": summary.student.id,
                    "term": summary.term,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentAttendanceSummaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, summary_id):
        try:
            return StudentAttendanceSummary.objects.select_related('student', 'academic_year').get(id=summary_id)
        except StudentAttendanceSummary.DoesNotExist:
            return None

    @extend_schema(
        tags=["Attendance - Summary"],
        responses={200: SummaryDetailResponseSerializer, 404: SummaryDetailResponseSerializer, 403: SummaryDetailResponseSerializer},
        description="Retrieve a single attendance summary by ID."
    )
    def get(self, request, summary_id):
        summary = self.get_object(summary_id)
        if not summary:
            return Response({
                "status": False,
                "message": "Attendance summary not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_summary(request.user, summary):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = StudentAttendanceSummaryDisplaySerializer(summary, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Attendance summary retrieved.",
            "data": {"summary": data}
        })

    @extend_schema(
        tags=["Attendance - Summary"],
        request=StudentAttendanceSummaryUpdateSerializer,
        responses={200: SummaryUpdateResponseSerializer, 400: SummaryUpdateResponseSerializer, 403: SummaryUpdateResponseSerializer},
        description="Update an attendance summary (manual adjustment)."
    )
    @transaction.atomic
    def put(self, request, summary_id):
        return self._update(request, summary_id, partial=False)

    @extend_schema(
        tags=["Attendance - Summary"],
        request=StudentAttendanceSummaryUpdateSerializer,
        responses={200: SummaryUpdateResponseSerializer, 400: SummaryUpdateResponseSerializer, 403: SummaryUpdateResponseSerializer},
        description="Partially update an attendance summary."
    )
    @transaction.atomic
    def patch(self, request, summary_id):
        return self._update(request, summary_id, partial=True)

    def _update(self, request, summary_id, partial):
        if not can_manage_summary(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        summary = self.get_object(summary_id)
        if not summary:
            return Response({
                "status": False,
                "message": "Attendance summary not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = StudentAttendanceSummaryUpdateSerializer(summary, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = StudentAttendanceSummaryDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Attendance summary updated.",
                "data": {"summary": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Attendance - Summary"],
        responses={200: SummaryDeleteResponseSerializer, 403: SummaryDeleteResponseSerializer, 404: SummaryDeleteResponseSerializer},
        description="Delete an attendance summary (admin only)."
    )
    @transaction.atomic
    def delete(self, request, summary_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        summary = self.get_object(summary_id)
        if not summary:
            return Response({
                "status": False,
                "message": "Attendance summary not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        success = StudentAttendanceSummaryService.delete_summary(summary)
        if success:
            return Response({
                "status": True,
                "message": "Attendance summary deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete attendance summary.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentAttendanceSummaryRecalculateView(APIView):
    permission_classes = [IsAuthenticated]

    class RecalculateSerializer(serializers.Serializer):
        start_date = serializers.DateField()
        end_date = serializers.DateField()

    @extend_schema(
        tags=["Attendance - Summary"],
        request=RecalculateSerializer,
        responses={200: SummaryRecalculateResponseSerializer, 400: SummaryRecalculateResponseSerializer, 403: SummaryRecalculateResponseSerializer},
        description="Recalculate attendance summary for a student based on raw attendance records within date range."
    )
    @transaction.atomic
    def post(self, request, summary_id):
        if not can_manage_summary(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        summary = StudentAttendanceSummaryService.get_summary_by_id(summary_id)
        if not summary:
            return Response({
                "status": False,
                "message": "Attendance summary not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.RecalculateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        updated = StudentAttendanceSummaryService.update_summary_from_attendance(
            student_id=summary.student.id,
            academic_year_id=summary.academic_year.id,
            term=summary.term,
            start_date=start_date,
            end_date=end_date
        )
        data = StudentAttendanceSummaryDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Attendance summary recalculated.",
            "data": {"summary": data}
        })