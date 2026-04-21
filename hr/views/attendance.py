import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from hr.models import EmployeeAttendance
from hr.serializers.attendance import (
    EmployeeAttendanceMinimalSerializer,
    EmployeeAttendanceCreateSerializer,
    EmployeeAttendanceUpdateSerializer,
    EmployeeAttendanceDisplaySerializer,
)
from hr.services.attendance import EmployeeAttendanceService

logger = logging.getLogger(__name__)

def can_view_attendance(user, attendance):
    if user.is_staff:
        return True
    if user.role in ['ADMIN', 'HR_MANAGER']:
        return True
    # Employees can view their own attendance
    if hasattr(user, 'employee_record'):
        return attendance.employee == user.employee_record
    return False

def can_manage_attendance(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AttendanceCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    employee = serializers.IntegerField()
    date = serializers.DateField()
    status = serializers.CharField()

class AttendanceCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttendanceCreateResponseData(allow_null=True)

class AttendanceUpdateResponseData(serializers.Serializer):
    attendance = EmployeeAttendanceDisplaySerializer()

class AttendanceUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttendanceUpdateResponseData(allow_null=True)

class AttendanceDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AttendanceDetailResponseData(serializers.Serializer):
    attendance = EmployeeAttendanceDisplaySerializer()

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
    results = EmployeeAttendanceMinimalSerializer(many=True)

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

class EmployeeAttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Attendance"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="employee_id", type=int, description="Filter by employee ID", required=False),
            OpenApiParameter(name="month", type=int, description="Filter by month (1-12)", required=False),
            OpenApiParameter(name="year", type=int, description="Filter by year", required=False),
        ],
        responses={200: AttendanceListResponseSerializer},
        description="List employee attendance records (admins/hr see all, employees see their own)."
    )
    def get(self, request):
        user = request.user
        employee_id = request.query_params.get("employee_id")
        month = request.query_params.get("month")
        year = request.query_params.get("year")

        if user.is_staff or can_manage_attendance(user):
            queryset = EmployeeAttendance.objects.all().select_related('employee', 'recorded_by')
        else:
            if hasattr(user, 'employee_record'):
                queryset = EmployeeAttendance.objects.filter(employee=user.employee_record)
            else:
                return Response({
                    "status": False,
                    "message": "Employee record not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if month:
            queryset = queryset.filter(date__month=month)
        if year:
            queryset = queryset.filter(date__year=year)

        queryset = queryset.order_by('-date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, EmployeeAttendanceMinimalSerializer)
        return Response({
            "status": True,
            "message": "Attendance records retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Attendance"],
        request=EmployeeAttendanceCreateSerializer,
        responses={201: AttendanceCreateResponseSerializer, 400: AttendanceCreateResponseSerializer, 403: AttendanceCreateResponseSerializer},
        description="Create an attendance record (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Set recorded_by to current user's employee record if exists
        data = request.data.copy()
        if hasattr(request.user, 'employee_record'):
            data['recorded_by_id'] = request.user.employee_record.id
        serializer = EmployeeAttendanceCreateSerializer(data=data)
        if serializer.is_valid():
            attendance = serializer.save()
            return Response({
                "status": True,
                "message": "Attendance record created.",
                "data": {
                    "id": attendance.id,
                    "employee": attendance.employee.id,
                    "date": attendance.date,
                    "status": attendance.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmployeeAttendanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, attendance_id):
        try:
            return EmployeeAttendance.objects.select_related('employee', 'recorded_by').get(id=attendance_id)
        except EmployeeAttendance.DoesNotExist:
            return None

    @extend_schema(
        tags=["HR - Attendance"],
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
        if not can_view_attendance(request.user, attendance):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = EmployeeAttendanceDisplaySerializer(attendance, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Attendance record retrieved.",
            "data": {"attendance": data}
        })

    @extend_schema(
        tags=["HR - Attendance"],
        request=EmployeeAttendanceUpdateSerializer,
        responses={200: AttendanceUpdateResponseSerializer, 400: AttendanceUpdateResponseSerializer, 403: AttendanceUpdateResponseSerializer},
        description="Update an attendance record (admin/hr only)."
    )
    @transaction.atomic
    def put(self, request, attendance_id):
        return self._update(request, attendance_id, partial=False)

    @extend_schema(
        tags=["HR - Attendance"],
        request=EmployeeAttendanceUpdateSerializer,
        responses={200: AttendanceUpdateResponseSerializer, 400: AttendanceUpdateResponseSerializer, 403: AttendanceUpdateResponseSerializer},
        description="Partially update an attendance record."
    )
    @transaction.atomic
    def patch(self, request, attendance_id):
        return self._update(request, attendance_id, partial=True)

    def _update(self, request, attendance_id, partial):
        if not can_manage_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeAttendanceUpdateSerializer(attendance, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EmployeeAttendanceDisplaySerializer(updated, context={"request": request}).data
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
        tags=["HR - Attendance"],
        responses={200: AttendanceDeleteResponseSerializer, 403: AttendanceDeleteResponseSerializer, 404: AttendanceDeleteResponseSerializer},
        description="Delete an attendance record (admin/hr only)."
    )
    @transaction.atomic
    def delete(self, request, attendance_id):
        if not can_manage_attendance(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = EmployeeAttendanceService.delete_attendance(attendance)
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