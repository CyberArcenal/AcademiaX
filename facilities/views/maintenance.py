import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from facilities.models import MaintenanceRequest
from facilities.serializers.maintenance import (
    MaintenanceRequestMinimalSerializer,
    MaintenanceRequestCreateSerializer,
    MaintenanceRequestUpdateSerializer,
    MaintenanceRequestDisplaySerializer,
)
from facilities.services.maintenance import MaintenanceRequestService

logger = logging.getLogger(__name__)

def can_view_maintenance(user, request_obj):
    if user.is_staff:
        return True
    # Users can see their own reported requests
    return request_obj.reported_by == user

def can_manage_maintenance(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN' or user.role == 'FACILITIES_MANAGER')

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class MaintenanceCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()

class MaintenanceCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MaintenanceCreateResponseData(allow_null=True)

class MaintenanceUpdateResponseData(serializers.Serializer):
    request = MaintenanceRequestDisplaySerializer()

class MaintenanceUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MaintenanceUpdateResponseData(allow_null=True)

class MaintenanceDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class MaintenanceDetailResponseData(serializers.Serializer):
    request = MaintenanceRequestDisplaySerializer()

class MaintenanceDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MaintenanceDetailResponseData(allow_null=True)

class MaintenanceListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = MaintenanceRequestMinimalSerializer(many=True)

class MaintenanceListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MaintenanceListResponseData()

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

class MaintenanceRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Facilities - Maintenance"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="facility_id", type=int, description="Filter by facility ID", required=False),
            OpenApiParameter(name="equipment_id", type=int, description="Filter by equipment ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by status", required=False),
            OpenApiParameter(name="priority", type=str, description="Filter by priority", required=False),
        ],
        responses={200: MaintenanceListResponseSerializer},
        description="List maintenance requests (admins see all, regular users see their own)."
    )
    def get(self, request):
        user = request.user
        facility_id = request.query_params.get("facility_id")
        equipment_id = request.query_params.get("equipment_id")
        status_filter = request.query_params.get("status")
        priority_filter = request.query_params.get("priority")

        if user.is_staff or can_manage_maintenance(user):
            queryset = MaintenanceRequest.objects.all().select_related('facility', 'equipment', 'reported_by', 'assigned_to')
        else:
            queryset = MaintenanceRequest.objects.filter(reported_by=user).select_related('facility', 'equipment')

        if facility_id:
            queryset = queryset.filter(facility_id=facility_id)
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, MaintenanceRequestMinimalSerializer)
        return Response({
            "status": True,
            "message": "Maintenance requests retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Facilities - Maintenance"],
        request=MaintenanceRequestCreateSerializer,
        responses={201: MaintenanceCreateResponseSerializer, 400: MaintenanceCreateResponseSerializer, 403: MaintenanceCreateResponseSerializer},
        description="Create a new maintenance request."
    )
    @transaction.atomic
    def post(self, request):
        # Ensure reported_by is set to current user
        data = request.data.copy()
        data['reported_by_id'] = request.user.id
        serializer = MaintenanceRequestCreateSerializer(data=data)
        if serializer.is_valid():
            request_obj = serializer.save()
            return Response({
                "status": True,
                "message": "Maintenance request created.",
                "data": {
                    "id": request_obj.id,
                    "title": request_obj.title,
                    "status": request_obj.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MaintenanceRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request_id):
        try:
            return MaintenanceRequest.objects.select_related('facility', 'equipment', 'reported_by', 'assigned_to').get(id=request_id)
        except MaintenanceRequest.DoesNotExist:
            return None

    @extend_schema(
        tags=["Facilities - Maintenance"],
        responses={200: MaintenanceDetailResponseSerializer, 404: MaintenanceDetailResponseSerializer, 403: MaintenanceDetailResponseSerializer},
        description="Retrieve a single maintenance request by ID."
    )
    def get(self, request, request_id):
        req = self.get_object(request_id)
        if not req:
            return Response({
                "status": False,
                "message": "Maintenance request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_maintenance(request.user, req):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = MaintenanceRequestDisplaySerializer(req, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Maintenance request retrieved.",
            "data": {"request": data}
        })

    @extend_schema(
        tags=["Facilities - Maintenance"],
        request=MaintenanceRequestUpdateSerializer,
        responses={200: MaintenanceUpdateResponseSerializer, 400: MaintenanceUpdateResponseSerializer, 403: MaintenanceUpdateResponseSerializer},
        description="Update a maintenance request (staff/facilities manager only)."
    )
    @transaction.atomic
    def put(self, request, request_id):
        return self._update(request, request_id, partial=False)

    @extend_schema(
        tags=["Facilities - Maintenance"],
        request=MaintenanceRequestUpdateSerializer,
        responses={200: MaintenanceUpdateResponseSerializer, 400: MaintenanceUpdateResponseSerializer, 403: MaintenanceUpdateResponseSerializer},
        description="Partially update a maintenance request."
    )
    @transaction.atomic
    def patch(self, request, request_id):
        return self._update(request, request_id, partial=True)

    def _update(self, request, request_id, partial):
        if not can_manage_maintenance(request.user):
            return Response({
                "status": False,
                "message": "Facilities manager or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        req = self.get_object(request_id)
        if not req:
            return Response({
                "status": False,
                "message": "Maintenance request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = MaintenanceRequestUpdateSerializer(req, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = MaintenanceRequestDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Maintenance request updated.",
                "data": {"request": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Facilities - Maintenance"],
        responses={200: MaintenanceDeleteResponseSerializer, 403: MaintenanceDeleteResponseSerializer, 404: MaintenanceDeleteResponseSerializer},
        description="Delete a maintenance request (admin only)."
    )
    @transaction.atomic
    def delete(self, request, request_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        req = self.get_object(request_id)
        if not req:
            return Response({
                "status": False,
                "message": "Maintenance request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = MaintenanceRequestService.delete_request(req)
        if success:
            return Response({
                "status": True,
                "message": "Maintenance request deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete maintenance request.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MaintenanceRequestStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    class StatusSerializer(serializers.Serializer):
        status = serializers.CharField()
        assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
        completed_date = serializers.DateField(required=False, allow_null=True)
        cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
        remarks = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["Facilities - Maintenance"],
        request=StatusSerializer,
        responses={200: MaintenanceUpdateResponseSerializer, 400: MaintenanceUpdateResponseSerializer, 403: MaintenanceUpdateResponseSerializer},
        description="Update maintenance request status (assign, complete, etc.) – staff only."
    )
    @transaction.atomic
    def post(self, request, request_id):
        if not can_manage_maintenance(request.user):
            return Response({
                "status": False,
                "message": "Facilities manager or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        req = MaintenanceRequestService.get_request_by_id(request_id)
        if not req:
            return Response({
                "status": False,
                "message": "Maintenance request not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.StatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        from users.models import User
        assigned_to = None
        if data.get('assigned_to_id'):
            try:
                assigned_to = User.objects.get(id=data['assigned_to_id'])
            except User.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "Assigned user not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        updated = MaintenanceRequestService.update_status(
            req,
            status=data['status'],
            assigned_to=assigned_to,
            completed_date=data.get('completed_date'),
            cost=data.get('cost'),
            remarks=data.get('remarks', '')
        )
        result_data = MaintenanceRequestDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Maintenance request status updated.",
            "data": {"request": result_data}
        })