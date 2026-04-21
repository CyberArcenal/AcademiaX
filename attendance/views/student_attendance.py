import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from attendance.models import StudentAttendance
from attendance.serializers.student_attendance import (
    StudentAttendanceMinimalSerializer,
    StudentAttendanceCreateSerializer,
    StudentAttendanceUpdateSerializer,
    StudentAttendanceDisplaySerializer,
)
from attendance.services.student_attendance import StudentAttendanceService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# Helper to check if user can mark attendance (teacher or admin)
def can_mark_attendance(user):
    return user.is_authenticated and (user.role == 'TEACHER' or user.is_staff)

def can_view_attendance_for_section(user, section):
    # Teacher can view their assigned sections; admin can view all; students can view own? Usually not.
    if user.is_staff:
        return True
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        # Check if teacher is assigned to this section
        return section.teacher_assignments.filter(teacher__user=user, is_active=True).exists()
    return False

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AttendanceCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    date = serializers.DateField()
    status = serializers.CharField()

class AttendanceCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttendanceCreateResponseData(allow_null=True)

class AttendanceUpdateResponseData(serializers.Serializer):
    attendance = StudentAttendanceDisplaySerializer()

class AttendanceUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttendanceUpdateResponseData(allow_null=True)

class AttendanceDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AttendanceDetailResponseData(serializers.Serializer):
    attendance = StudentAttendanceDisplaySerializer()

class AttendanceDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttendanceDetailResponseData(allow_null=True)

class AttendanceListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = StudentAttendanceMinimalSerializer(many=True)

class AttendanceListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttendanceListResponseData()

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

class StudentAttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Attendance - Student"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="section_id", type=int, description="Filter by section ID", required=False),
            OpenApiParameter(name="date", type=str, description="Filter by date (YYYY-MM-DD)", required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
        ],
        responses={200: AttendanceListResponseSerializer},
        description="List student attendance records (teachers see their sections, admins see all)."
    )
    def get(self, request):
        user = request.user
        section_id = request.query_params.get("section_id")
        date = request.query_params.get("date")
        student_id = request.query_params.get("student_id")

        queryset = StudentAttendance.objects.all().select_related('student', 'section', 'subject', 'academic_year')
        if not user.is_staff:
            if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                # Restrict to sections taught by this teacher
                teacher = user.teacher_profile
                assigned_section_ids = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                queryset = queryset.filter(section_id__in=assigned_section_ids)
            elif user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                # Students can only see their own attendance
                queryset = queryset.filter(student=user.student_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if date:
            queryset = queryset.filter(date=date)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, StudentAttendanceMinimalSerializer)
        return Response({
            "status": True,
            "message": "Attendance records retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Attendance - Student"],
        request=StudentAttendanceCreateSerializer,
        responses={201: AttendanceCreateResponseSerializer, 400: AttendanceCreateResponseSerializer, 403: AttendanceCreateResponseSerializer},
        description="Create a student attendance record (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_mark_attendance(request.user):
            return Response({
                "status": False,
                "message": "Permission denied. Only teachers and admins can mark attendance.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = StudentAttendanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            attendance = serializer.save()
            return Response({
                "status": True,
                "message": "Attendance recorded.",
                "data": {
                    "id": attendance.id,
                    "student": attendance.student.id,
                    "date": attendance.date,
                    "status": attendance.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentAttendanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, attendance_id):
        try:
            return StudentAttendance.objects.select_related('student', 'section', 'subject').get(id=attendance_id)
        except StudentAttendance.DoesNotExist:
            return None

    @extend_schema(
        tags=["Attendance - Student"],
        responses={200: AttendanceDetailResponseSerializer, 404: AttendanceDetailResponseSerializer, 403: AttendanceDetailResponseSerializer},
        description="Retrieve a single attendance record by ID."
    )
    def get(self, request, attendance_id):
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Check permissions
        user = request.user
        if not (user.is_staff or (user.role == 'TEACHER' and can_view_attendance_for_section(user, attendance.section)) or (user.role == 'STUDENT' and attendance.student.user == user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        data = StudentAttendanceDisplaySerializer(attendance, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Attendance record retrieved.",
            "data": {"attendance": data}
        })

    @extend_schema(
        tags=["Attendance - Student"],
        request=StudentAttendanceUpdateSerializer,
        responses={200: AttendanceUpdateResponseSerializer, 400: AttendanceUpdateResponseSerializer, 403: AttendanceUpdateResponseSerializer},
        description="Update an attendance record (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, attendance_id):
        return self._update(request, attendance_id, partial=False)

    @extend_schema(
        tags=["Attendance - Student"],
        request=StudentAttendanceUpdateSerializer,
        responses={200: AttendanceUpdateResponseSerializer, 400: AttendanceUpdateResponseSerializer, 403: AttendanceUpdateResponseSerializer},
        description="Partially update an attendance record."
    )
    @transaction.atomic
    def patch(self, request, attendance_id):
        return self._update(request, attendance_id, partial=True)

    def _update(self, request, attendance_id, partial):
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_mark_attendance(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = StudentAttendanceUpdateSerializer(attendance, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = StudentAttendanceDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Attendance record updated.",
                "data": {"attendance": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Attendance - Student"],
        responses={200: AttendanceDeleteResponseSerializer, 403: AttendanceDeleteResponseSerializer, 404: AttendanceDeleteResponseSerializer},
        description="Delete an attendance record (teacher or admin only)."
    )
    @transaction.atomic
    def delete(self, request, attendance_id):
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_mark_attendance(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = StudentAttendanceService.delete_attendance(attendance)
        if success:
            return Response({
                "status": True,
                "message": "Attendance record deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete attendance record.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkAttendanceMarkView(APIView):
    permission_classes = [IsAuthenticated]

    class BulkMarkSerializer(serializers.Serializer):
        section_id = serializers.IntegerField()
        subject_id = serializers.IntegerField()
        academic_year_id = serializers.IntegerField()
        date = serializers.DateField()
        attendance_list = serializers.ListField(
            child=serializers.DictField()
        )

    @extend_schema(
        tags=["Attendance - Student"],
        request=BulkMarkSerializer,
        responses={201: serializers.Serializer, 400: serializers.Serializer, 403: serializers.Serializer},
        description="Bulk mark attendance for multiple students (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_mark_attendance(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.BulkMarkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        section_id = data['section_id']
        subject_id = data['subject_id']
        academic_year_id = data['academic_year_id']
        date = data['date']
        attendance_list = data['attendance_list']

        # Convert to list of dicts for bulk create
        attendance_objects = []
        for item in attendance_list:
            attendance_objects.append({
                'student_id': item['student_id'],
                'section_id': section_id,
                'subject_id': subject_id,
                'academic_year_id': academic_year_id,
                'date': date,
                'status': item.get('status', 'PR'),
                'time_in': item.get('time_in'),
                'time_out': item.get('time_out'),
                'late_minutes': item.get('late_minutes', 0),
                'late_reason': item.get('late_reason'),
                'remarks': item.get('remarks', ''),
                'marked_by': request.user.teacher_profile if request.user.role == 'TEACHER' else None,
            })

        created = StudentAttendanceService.bulk_create_attendance(attendance_objects)
        return Response({
            "status": True,
            "message": f"{len(created)} attendance records created.",
            "data": {"count": len(created)}
        }, status=status.HTTP_201_CREATED)