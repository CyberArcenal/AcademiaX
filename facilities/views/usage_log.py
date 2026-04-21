import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from facilities.models import FacilityUsageLog
from facilities.serializers.usage_log import (
    FacilityUsageLogMinimalSerializer,
    FacilityUsageLogCreateSerializer,
    FacilityUsageLogUpdateSerializer,
    FacilityUsageLogDisplaySerializer,
)
from facilities.services.usage_log import FacilityUsageLogService

logger = logging.getLogger(__name__)

def can_view_usage_log(user, log):
    if user.is_staff:
        return True
    # Users can see logs they created (used_by)
    return log.used_by == user

def can_manage_usage_log(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'FACILITIES_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class UsageLogCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    facility = serializers.IntegerField()
    check_in = serializers.DateTimeField()

class UsageLogCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UsageLogCreateResponseData(allow_null=True)

class UsageLogUpdateResponseData(serializers.Serializer):
    log = FacilityUsageLogDisplaySerializer()

class UsageLogUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UsageLogUpdateResponseData(allow_null=True)

class UsageLogDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class UsageLogDetailResponseData(serializers.Serializer):
    log = FacilityUsageLogDisplaySerializer()

class UsageLogDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UsageLogDetailResponseData(allow_null=True)

class UsageLogListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = FacilityUsageLogMinimalSerializer(many=True)

class UsageLogListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UsageLogListResponseData()

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

class FacilityUsageLogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Facilities - Usage Logs"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="facility_id", type=int, description="Filter by facility ID", required=False),
            OpenApiParameter(name="reservation_id", type=int, description="Filter by reservation ID", required=False),
        ],
        responses={200: UsageLogListResponseSerializer},
        description="List facility usage logs (admins see all, regular users see their own)."
    )
    def get(self, request):
        user = request.user
        facility_id = request.query_params.get("facility_id")
        reservation_id = request.query_params.get("reservation_id")

        if user.is_staff or can_manage_usage_log(user):
            queryset = FacilityUsageLog.objects.all().select_related('facility', 'reservation', 'used_by')
        else:
            queryset = FacilityUsageLog.objects.filter(used_by=user).select_related('facility', 'reservation')

        if facility_id:
            queryset = queryset.filter(facility_id=facility_id)
        if reservation_id:
            queryset = queryset.filter(reservation_id=reservation_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, FacilityUsageLogMinimalSerializer)
        return Response({
            "status": True,
            "message": "Usage logs retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Facilities - Usage Logs"],
        request=FacilityUsageLogCreateSerializer,
        responses={201: UsageLogCreateResponseSerializer, 400: UsageLogCreateResponseSerializer, 403: UsageLogCreateResponseSerializer},
        description="Create a new facility usage log (check-in)."
    )
    @transaction.atomic
    def post(self, request):
        # Set used_by to current user
        data = request.data.copy()
        data['used_by_id'] = request.user.id
        serializer = FacilityUsageLogCreateSerializer(data=data)
        if serializer.is_valid():
            log = serializer.save()
            return Response({
                "status": True,
                "message": "Usage log created (checked in).",
                "data": {
                    "id": log.id,
                    "facility": log.facility.id,
                    "check_in": log.check_in,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FacilityUsageLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, log_id):
        try:
            return FacilityUsageLog.objects.select_related('facility', 'reservation', 'used_by').get(id=log_id)
        except FacilityUsageLog.DoesNotExist:
            return None

    @extend_schema(
        tags=["Facilities - Usage Logs"],
        responses={200: UsageLogDetailResponseSerializer, 404: UsageLogDetailResponseSerializer, 403: UsageLogDetailResponseSerializer},
        description="Retrieve a single usage log by ID."
    )
    def get(self, request, log_id):
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Usage log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_usage_log(request.user, log):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = FacilityUsageLogDisplaySerializer(log, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Usage log retrieved.",
            "data": {"log": data}
        })

    @extend_schema(
        tags=["Facilities - Usage Logs"],
        request=FacilityUsageLogUpdateSerializer,
        responses={200: UsageLogUpdateResponseSerializer, 400: UsageLogUpdateResponseSerializer, 403: UsageLogUpdateResponseSerializer},
        description="Update a usage log (e.g., check-out)."
    )
    @transaction.atomic
    def put(self, request, log_id):
        return self._update(request, log_id, partial=False)

    @extend_schema(
        tags=["Facilities - Usage Logs"],
        request=FacilityUsageLogUpdateSerializer,
        responses={200: UsageLogUpdateResponseSerializer, 400: UsageLogUpdateResponseSerializer, 403: UsageLogUpdateResponseSerializer},
        description="Partially update a usage log (check-out)."
    )
    @transaction.atomic
    def patch(self, request, log_id):
        return self._update(request, log_id, partial=True)

    def _update(self, request, log_id, partial):
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Usage log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Only the user who checked in or staff can update
        user = request.user
        if not (user.is_staff or can_manage_usage_log(user) or log.used_by == user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = FacilityUsageLogUpdateSerializer(log, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = FacilityUsageLogDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Usage log updated.",
                "data": {"log": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Facilities - Usage Logs"],
        responses={200: UsageLogDeleteResponseSerializer, 403: UsageLogDeleteResponseSerializer, 404: UsageLogDeleteResponseSerializer},
        description="Delete a usage log (admin only)."
    )
    @transaction.atomic
    def delete(self, request, log_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Usage log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = FacilityUsageLogService.delete_log(log)
        if success:
            return Response({
                "status": True,
                "message": "Usage log deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete usage log.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FacilityUsageLogCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    class CheckoutSerializer(serializers.Serializer):
        condition_after = serializers.CharField(required=False, allow_blank=True)
        notes = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["Facilities - Usage Logs"],
        request=CheckoutSerializer,
        responses={200: UsageLogUpdateResponseSerializer, 400: UsageLogUpdateResponseSerializer, 403: UsageLogUpdateResponseSerializer},
        description="Check out from a facility (update check_out time)."
    )
    @transaction.atomic
    def post(self, request, log_id):
        log = FacilityUsageLogService.get_log_by_id(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Usage log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not (user.is_staff or can_manage_usage_log(user) or log.used_by == user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if log.check_out:
            return Response({
                "status": False,
                "message": "Already checked out.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = FacilityUsageLogService.check_out(log, 
            condition_after=serializer.validated_data.get('condition_after', ''),
            notes=serializer.validated_data.get('notes', '')
        )
        data = FacilityUsageLogDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Checked out.",
            "data": {"log": data}
        })