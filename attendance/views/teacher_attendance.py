import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from attendance.models import TeacherAttendance
from attendance.serializers.teacher_attendance import (
    TeacherAttendanceMinimalSerializer,
    TeacherAttendanceCreateSerializer,
    TeacherAttendanceUpdateSerializer,
    TeacherAttendanceDisplaySerializer,
)
from attendance.services.teacher_attendance import TeacherAttendanceService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# Helper to check if user can manage teacher attendance (admin only)
def can_manage_teacher_attendance(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TeacherAttendanceCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    teacher = serializers.IntegerField()
    date = serializers.DateField()
    status = serializers.CharField()

class TeacherAttendanceCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherAttendanceCreateResponseData(allow_null=True)

class TeacherAttendanceUpdateResponseData(serializers.Serializer):
    attendance = TeacherAttendanceDisplaySerializer()

class TeacherAttendanceUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherAttendanceUpdateResponseData(allow_null=True)

class TeacherAttendanceDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TeacherAttendanceDetailResponseData(serializers.Serializer):
    attendance = TeacherAttendanceDisplaySerializer()

class TeacherAttendanceDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherAttendanceDetailResponseData(allow_null=True)

class TeacherAttendanceListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TeacherAttendanceMinimalSerializer(many=True)

class TeacherAttendanceListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherAttendanceListResponseData()

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

class TeacherAttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Attendance - Teacher"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="teacher_id", type=int, description="Filter by teacher ID", required=False),
            OpenApiParameter(name="date", type=str, description="Filter by date (YYYY-MM-DD)", required=False),
        ],
        responses={200: TeacherAttendanceListResponseSerializer},
        description="List teacher attendance records (admin only)."
    )
    def get(self, request):
        if not can_manage_teacher_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        teacher_id = request.query_params.get("teacher_id")
        date = request.query_params.get("date")
        queryset = TeacherAttendance.objects.all().select_related('teacher', 'recorded_by')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if date:
            queryset = queryset.filter(date=date)
        queryset = queryset.order_by('-date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, TeacherAttendanceMinimalSerializer)
        return Response({
            "status": True,
            "message": "Teacher attendance records retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Attendance - Teacher"],
        request=TeacherAttendanceCreateSerializer,
        responses={201: TeacherAttendanceCreateResponseSerializer, 400: TeacherAttendanceCreateResponseSerializer, 403: TeacherAttendanceCreateResponseSerializer},
        description="Create a teacher attendance record (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_teacher_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = TeacherAttendanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            attendance = serializer.save()
            return Response({
                "status": True,
                "message": "Teacher attendance recorded.",
                "data": {
                    "id": attendance.id,
                    "teacher": attendance.teacher.id,
                    "date": attendance.date,
                    "status": attendance.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeacherAttendanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, attendance_id):
        try:
            return TeacherAttendance.objects.select_related('teacher', 'recorded_by').get(id=attendance_id)
        except TeacherAttendance.DoesNotExist:
            return None

    @extend_schema(
        tags=["Attendance - Teacher"],
        responses={200: TeacherAttendanceDetailResponseSerializer, 404: TeacherAttendanceDetailResponseSerializer, 403: TeacherAttendanceDetailResponseSerializer},
        description="Retrieve a single teacher attendance record by ID (admin only)."
    )
    def get(self, request, attendance_id):
        if not can_manage_teacher_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Teacher attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = TeacherAttendanceDisplaySerializer(attendance, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Teacher attendance record retrieved.",
            "data": {"attendance": data}
        })

    @extend_schema(
        tags=["Attendance - Teacher"],
        request=TeacherAttendanceUpdateSerializer,
        responses={200: TeacherAttendanceUpdateResponseSerializer, 400: TeacherAttendanceUpdateResponseSerializer, 403: TeacherAttendanceUpdateResponseSerializer},
        description="Update a teacher attendance record (admin only)."
    )
    @transaction.atomic
    def put(self, request, attendance_id):
        return self._update(request, attendance_id, partial=False)

    @extend_schema(
        tags=["Attendance - Teacher"],
        request=TeacherAttendanceUpdateSerializer,
        responses={200: TeacherAttendanceUpdateResponseSerializer, 400: TeacherAttendanceUpdateResponseSerializer, 403: TeacherAttendanceUpdateResponseSerializer},
        description="Partially update a teacher attendance record."
    )
    @transaction.atomic
    def patch(self, request, attendance_id):
        return self._update(request, attendance_id, partial=True)

    def _update(self, request, attendance_id, partial):
        if not can_manage_teacher_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Teacher attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TeacherAttendanceUpdateSerializer(attendance, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = TeacherAttendanceDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Teacher attendance record updated.",
                "data": {"attendance": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Attendance - Teacher"],
        responses={200: TeacherAttendanceDeleteResponseSerializer, 403: TeacherAttendanceDeleteResponseSerializer, 404: TeacherAttendanceDeleteResponseSerializer},
        description="Delete a teacher attendance record (admin only)."
    )
    @transaction.atomic
    def delete(self, request, attendance_id):
        if not can_manage_teacher_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Teacher attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        success = TeacherAttendanceService.delete_attendance(attendance)
        if success:
            return Response({
                "status": True,
                "message": "Teacher attendance record deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete teacher attendance record.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)