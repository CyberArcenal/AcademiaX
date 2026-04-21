import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from hr.models import LeaveRequest
from hr.serializers.leave import (
    LeaveRequestMinimalSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestUpdateSerializer,
    LeaveRequestDisplaySerializer,
)
from hr.services.leave import LeaveRequestService

logger = logging.getLogger(__name__)

def can_view_leave(user, leave):
    if user.is_staff:
        return True
    if user.role in ['ADMIN', 'HR_MANAGER']:
        return True
    # Employees can view their own leave requests
    if hasattr(user, 'employee_record'):
        return leave.employee == user.employee_record
    return False

def can_manage_leave(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class LeaveCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    employee = serializers.IntegerField()
    leave_type = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField()

class LeaveCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LeaveCreateResponseData(allow_null=True)

class LeaveUpdateResponseData(serializers.Serializer):
    leave = LeaveRequestDisplaySerializer()

class LeaveUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LeaveUpdateResponseData(allow_null=True)

class LeaveDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class LeaveDetailResponseData(serializers.Serializer):
    leave = LeaveRequestDisplaySerializer()

class LeaveDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LeaveDetailResponseData(allow_null=True)

class LeaveListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = LeaveRequestMinimalSerializer(many=True)

class LeaveListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LeaveListResponseData()

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

class LeaveRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Leave"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="employee_id", type=int, description="Filter by employee ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by status", required=False),
            OpenApiParameter(name="year", type=int, description="Filter by year (start_date)", required=False),
        ],
        responses={200: LeaveListResponseSerializer},
        description="List leave requests (admins/hr see all, employees see their own)."
    )
    def get(self, request):
        user = request.user
        employee_id = request.query_params.get("employee_id")
        status_filter = request.query_params.get("status")
        year = request.query_params.get("year")

        if user.is_staff or can_manage_leave(user):
            queryset = LeaveRequest.objects.all().select_related('employee', 'approved_by')
        else:
            if hasattr(user, 'employee_record'):
                queryset = LeaveRequest.objects.filter(employee=user.employee_record)
            else:
                return Response({
                    "status": False,
                    "message": "Employee record not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if year:
            queryset = queryset.filter(start_date__year=year)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, LeaveRequestMinimalSerializer)
        return Response({
            "status": True,
            "message": "Leave requests retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Leave"],
        request=LeaveRequestCreateSerializer,
        responses={201: LeaveCreateResponseSerializer, 400: LeaveCreateResponseSerializer, 403: LeaveCreateResponseSerializer},
        description="Create a leave request (employee can create for themselves, admin/hr for others)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # For employees, they can only create for themselves; admin/hr can specify employee_id
        data = request.data.copy()
        if not can_manage_leave(request.user):
            if hasattr(request.user, 'employee_record'):
                data['employee_id'] = request.user.employee_record.id
            else:
                return Response({
                    "status": False,
                    "message": "Employee record not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        serializer = LeaveRequestCreateSerializer(data=data)
        if serializer.is_valid():
            leave = serializer.save()
            return Response({
                "status": True,
                "message": "Leave request created.",
                "data": {
                    "id": leave.id,
                    "employee": leave.employee.id,
                    "leave_type": leave.leave_type,
                    "start_date": leave.start_date,
                    "end_date": leave.end_date,
                    "status": leave.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LeaveRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, leave_id):
        try:
            return LeaveRequest.objects.select_related('employee', 'approved_by').get(id=leave_id)
        except LeaveRequest.DoesNotExist:
            return None

    @extend_schema(
        tags=["HR - Leave"],
        responses={200: LeaveDetailResponseSerializer, 404: LeaveDetailResponseSerializer, 403: LeaveDetailResponseSerializer},
        description="Retrieve a single leave request by ID."
    )
    def get(self, request, leave_id):
        leave = self.get_object(leave_id)
        if not leave:
            return Response({
                "status": False,
                "message": "Leave request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_leave(request.user, leave):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = LeaveRequestDisplaySerializer(leave, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Leave request retrieved.",
            "data": {"leave": data}
        })

    @extend_schema(
        tags=["HR - Leave"],
        request=LeaveRequestUpdateSerializer,
        responses={200: LeaveUpdateResponseSerializer, 400: LeaveUpdateResponseSerializer, 403: LeaveUpdateResponseSerializer},
        description="Update a leave request (admin/hr only, or employee while pending)."
    )
    @transaction.atomic
    def put(self, request, leave_id):
        return self._update(request, leave_id, partial=False)

    @extend_schema(
        tags=["HR - Leave"],
        request=LeaveRequestUpdateSerializer,
        responses={200: LeaveUpdateResponseSerializer, 400: LeaveUpdateResponseSerializer, 403: LeaveUpdateResponseSerializer},
        description="Partially update a leave request."
    )
    @transaction.atomic
    def patch(self, request, leave_id):
        return self._update(request, leave_id, partial=True)

    def _update(self, request, leave_id, partial):
        leave = self.get_object(leave_id)
        if not leave:
            return Response({
                "status": False,
                "message": "Leave request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        # Allow employee to edit if still pending, admin/hr always allowed
        if can_manage_leave(user):
            pass
        elif hasattr(user, 'employee_record') and leave.employee == user.employee_record and leave.status == 'PND':
            pass
        else:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = LeaveRequestUpdateSerializer(leave, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = LeaveRequestDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Leave request updated.",
                "data": {"leave": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["HR - Leave"],
        responses={200: LeaveDeleteResponseSerializer, 403: LeaveDeleteResponseSerializer, 404: LeaveDeleteResponseSerializer},
        description="Delete a leave request (admin/hr only)."
    )
    @transaction.atomic
    def delete(self, request, leave_id):
        if not can_manage_leave(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        leave = self.get_object(leave_id)
        if not leave:
            return Response({
                "status": False,
                "message": "Leave request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = LeaveRequestService.delete_leave(leave)
        if success:
            return Response({
                "status": True,
                "message": "Leave request deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete leave request.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LeaveRequestApproveView(APIView):
    permission_classes = [IsAuthenticated]

    class ApproveSerializer(serializers.Serializer):
        remarks = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["HR - Leave"],
        request=ApproveSerializer,
        responses={200: LeaveUpdateResponseSerializer, 400: LeaveUpdateResponseSerializer, 403: LeaveUpdateResponseSerializer},
        description="Approve a leave request (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request, leave_id):
        if not can_manage_leave(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        leave = LeaveRequestService.get_leave_by_id(leave_id)
        if not leave:
            return Response({
                "status": False,
                "message": "Leave request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if leave.status != 'PND':
            return Response({
                "status": False,
                "message": "Only pending leave requests can be approved.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.ApproveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = LeaveRequestService.update_leave_status(
            leave, 'APP', approved_by=request.user.employee_record, remarks=serializer.validated_data.get('remarks', '')
        )
        data = LeaveRequestDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Leave request approved.",
            "data": {"leave": data}
        })


class LeaveRequestRejectView(APIView):
    permission_classes = [IsAuthenticated]

    class RejectSerializer(serializers.Serializer):
        remarks = serializers.CharField(required=True)

    @extend_schema(
        tags=["HR - Leave"],
        request=RejectSerializer,
        responses={200: LeaveUpdateResponseSerializer, 400: LeaveUpdateResponseSerializer, 403: LeaveUpdateResponseSerializer},
        description="Reject a leave request (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request, leave_id):
        if not can_manage_leave(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        leave = LeaveRequestService.get_leave_by_id(leave_id)
        if not leave:
            return Response({
                "status": False,
                "message": "Leave request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if leave.status != 'PND':
            return Response({
                "status": False,
                "message": "Only pending leave requests can be rejected.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.RejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = LeaveRequestService.update_leave_status(
            leave, 'REJ', approved_by=request.user.employee_record, remarks=serializer.validated_data['remarks']
        )
        data = LeaveRequestDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Leave request rejected.",
            "data": {"leave": data}
        })