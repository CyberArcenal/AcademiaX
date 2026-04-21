import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from communication.models import BroadcastLog
from communication.serializers.broadcast_log import (
    BroadcastLogMinimalSerializer,
    BroadcastLogCreateSerializer,
    BroadcastLogUpdateSerializer,
    BroadcastLogDisplaySerializer,
)
from communication.services.broadcast_log import BroadcastLogService

logger = logging.getLogger(__name__)

def can_manage_broadcast_logs(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN')

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class BroadcastLogCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    announcement = serializers.IntegerField()
    recipient = serializers.IntegerField()
    channel = serializers.CharField()

class BroadcastLogCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BroadcastLogCreateResponseData(allow_null=True)

class BroadcastLogUpdateResponseData(serializers.Serializer):
    log = BroadcastLogDisplaySerializer()

class BroadcastLogUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BroadcastLogUpdateResponseData(allow_null=True)

class BroadcastLogDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class BroadcastLogDetailResponseData(serializers.Serializer):
    log = BroadcastLogDisplaySerializer()

class BroadcastLogDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BroadcastLogDetailResponseData(allow_null=True)

class BroadcastLogListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = BroadcastLogMinimalSerializer(many=True)

class BroadcastLogListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BroadcastLogListResponseData()

class BroadcastLogRetryResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BroadcastLogDetailResponseData()

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

class BroadcastLogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="announcement_id", type=int, description="Filter by announcement ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by status (PENDING, SENT, FAILED)", required=False),
        ],
        responses={200: BroadcastLogListResponseSerializer},
        description="List broadcast logs (admin only)."
    )
    def get(self, request):
        if not can_manage_broadcast_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        announcement_id = request.query_params.get("announcement_id")
        status_filter = request.query_params.get("status")
        queryset = BroadcastLog.objects.all().select_related('announcement', 'recipient')
        if announcement_id:
            queryset = queryset.filter(announcement_id=announcement_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, BroadcastLogMinimalSerializer)
        return Response({
            "status": True,
            "message": "Broadcast logs retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        request=BroadcastLogCreateSerializer,
        responses={201: BroadcastLogCreateResponseSerializer, 400: BroadcastLogCreateResponseSerializer, 403: BroadcastLogCreateResponseSerializer},
        description="Create a broadcast log (usually internal, but available for manual retries)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_broadcast_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = BroadcastLogCreateSerializer(data=request.data)
        if serializer.is_valid():
            log = serializer.save()
            return Response({
                "status": True,
                "message": "Broadcast log created.",
                "data": {
                    "id": log.id,
                    "announcement": log.announcement.id,
                    "recipient": log.recipient.id,
                    "channel": log.channel,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BroadcastLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, log_id):
        try:
            return BroadcastLog.objects.select_related('announcement', 'recipient').get(id=log_id)
        except BroadcastLog.DoesNotExist:
            return None

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        responses={200: BroadcastLogDetailResponseSerializer, 404: BroadcastLogDetailResponseSerializer, 403: BroadcastLogDetailResponseSerializer},
        description="Retrieve a single broadcast log by ID (admin only)."
    )
    def get(self, request, log_id):
        if not can_manage_broadcast_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Broadcast log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = BroadcastLogDisplaySerializer(log, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Broadcast log retrieved.",
            "data": {"log": data}
        })

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        request=BroadcastLogUpdateSerializer,
        responses={200: BroadcastLogUpdateResponseSerializer, 400: BroadcastLogUpdateResponseSerializer, 403: BroadcastLogUpdateResponseSerializer},
        description="Update a broadcast log (e.g., mark as sent)."
    )
    @transaction.atomic
    def put(self, request, log_id):
        return self._update(request, log_id, partial=False)

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        request=BroadcastLogUpdateSerializer,
        responses={200: BroadcastLogUpdateResponseSerializer, 400: BroadcastLogUpdateResponseSerializer, 403: BroadcastLogUpdateResponseSerializer},
        description="Partially update a broadcast log."
    )
    @transaction.atomic
    def patch(self, request, log_id):
        return self._update(request, log_id, partial=True)

    def _update(self, request, log_id, partial):
        if not can_manage_broadcast_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Broadcast log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = BroadcastLogUpdateSerializer(log, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = BroadcastLogDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Broadcast log updated.",
                "data": {"log": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        responses={200: BroadcastLogDeleteResponseSerializer, 403: BroadcastLogDeleteResponseSerializer, 404: BroadcastLogDeleteResponseSerializer},
        description="Delete a broadcast log (admin only)."
    )
    @transaction.atomic
    def delete(self, request, log_id):
        if not can_manage_broadcast_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Broadcast log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = BroadcastLogService.delete_log(log)
        if success:
            return Response({
                "status": True,
                "message": "Broadcast log deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete broadcast log.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastLogRetryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        responses={200: BroadcastLogRetryResponseSerializer, 403: BroadcastLogRetryResponseSerializer, 404: BroadcastLogRetryResponseSerializer},
        description="Retry a failed broadcast log (admin only)."
    )
    @transaction.atomic
    def post(self, request, log_id):
        if not can_manage_broadcast_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = BroadcastLogService.get_log_by_id(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Broadcast log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if log.status != 'FAILED':
            return Response({
                "status": False,
                "message": "Only failed logs can be retried.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = BroadcastLogService.retry_failed(log)
        data = BroadcastLogDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Broadcast log marked for retry.",
            "data": {"log": data}
        })


class BroadcastLogFailedView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Broadcast Logs"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: BroadcastLogListResponseSerializer},
        description="List all failed broadcast logs (admin only)."
    )
    def get(self, request):
        if not can_manage_broadcast_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        logs = BroadcastLogService.get_failed_logs()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(logs, request)
        data = wrap_paginated_data(paginator, page, request, BroadcastLogMinimalSerializer)
        return Response({
            "status": True,
            "message": "Failed broadcast logs retrieved.",
            "data": data
        })