import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from communication.models import Notification
from communication.serializers.notification import (
    NotificationMinimalSerializer,
    NotificationCreateSerializer,
    NotificationUpdateSerializer,
    NotificationDisplaySerializer,
)
from communication.services.notification import NotificationService

logger = logging.getLogger(__name__)

# Helper to check if user can view notification (only recipient or staff)
def can_view_notification(user, notification):
    if user.is_staff:
        return True
    return notification.recipient == user

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class NotificationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    recipient = serializers.IntegerField()

class NotificationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = NotificationCreateResponseData(allow_null=True)

class NotificationUpdateResponseData(serializers.Serializer):
    notification = NotificationDisplaySerializer()

class NotificationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = NotificationUpdateResponseData(allow_null=True)

class NotificationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class NotificationDetailResponseData(serializers.Serializer):
    notification = NotificationDisplaySerializer()

class NotificationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = NotificationDetailResponseData(allow_null=True)

class NotificationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = NotificationMinimalSerializer(many=True)

class NotificationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = NotificationListResponseData()

class UnreadCountResponseData(serializers.Serializer):
    unread_count = serializers.IntegerField()

class UnreadCountResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UnreadCountResponseData()

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

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Notifications"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="unread_only", type=bool, description="Only unread notifications", required=False),
        ],
        responses={200: NotificationListResponseSerializer},
        description="List notifications for the authenticated user."
    )
    def get(self, request):
        user = request.user
        unread_only = request.query_params.get("unread_only", "false").lower() == "true"
        notifications = NotificationService.get_user_notifications(user.id, unread_only=unread_only)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(notifications, request)
        data = wrap_paginated_data(paginator, page, request, NotificationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Notifications retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Communication - Notifications"],
        request=NotificationCreateSerializer,
        responses={201: NotificationCreateResponseSerializer, 400: NotificationCreateResponseSerializer, 403: NotificationCreateResponseSerializer},
        description="Create a notification (typically internal, but available for staff)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Staff permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = NotificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            notification = serializer.save()
            return Response({
                "status": True,
                "message": "Notification created.",
                "data": {
                    "id": notification.id,
                    "title": notification.title,
                    "recipient": notification.recipient.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, notification_id):
        try:
            return Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return None

    @extend_schema(
        tags=["Communication - Notifications"],
        responses={200: NotificationDetailResponseSerializer, 404: NotificationDetailResponseSerializer, 403: NotificationDetailResponseSerializer},
        description="Retrieve a single notification by ID (only recipient or staff)."
    )
    def get(self, request, notification_id):
        notification = self.get_object(notification_id)
        if not notification:
            return Response({
                "status": False,
                "message": "Notification not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_notification(request.user, notification):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = NotificationDisplaySerializer(notification, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Notification retrieved.",
            "data": {"notification": data}
        })

    @extend_schema(
        tags=["Communication - Notifications"],
        request=NotificationUpdateSerializer,
        responses={200: NotificationUpdateResponseSerializer, 400: NotificationUpdateResponseSerializer, 403: NotificationUpdateResponseSerializer},
        description="Update a notification (mark read)."
    )
    @transaction.atomic
    def put(self, request, notification_id):
        return self._update(request, notification_id, partial=False)

    @extend_schema(
        tags=["Communication - Notifications"],
        request=NotificationUpdateSerializer,
        responses={200: NotificationUpdateResponseSerializer, 400: NotificationUpdateResponseSerializer, 403: NotificationUpdateResponseSerializer},
        description="Partially update a notification (mark read)."
    )
    @transaction.atomic
    def patch(self, request, notification_id):
        return self._update(request, notification_id, partial=True)

    def _update(self, request, notification_id, partial):
        notification = self.get_object(notification_id)
        if not notification:
            return Response({
                "status": False,
                "message": "Notification not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_notification(request.user, notification):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = NotificationUpdateSerializer(notification, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = NotificationDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Notification updated.",
                "data": {"notification": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Communication - Notifications"],
        responses={200: NotificationDeleteResponseSerializer, 403: NotificationDeleteResponseSerializer, 404: NotificationDeleteResponseSerializer},
        description="Delete a notification (user can delete their own)."
    )
    @transaction.atomic
    def delete(self, request, notification_id):
        notification = self.get_object(notification_id)
        if not notification:
            return Response({
                "status": False,
                "message": "Notification not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_notification(request.user, notification):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = NotificationService.delete_notification(notification)
        if success:
            return Response({
                "status": True,
                "message": "Notification deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete notification.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Notifications"],
        responses={200: NotificationDetailResponseSerializer, 403: NotificationDetailResponseSerializer, 404: NotificationDetailResponseSerializer},
        description="Mark a single notification as read."
    )
    @transaction.atomic
    def post(self, request, notification_id):
        notification = NotificationService.get_notification_by_id(notification_id)
        if not notification:
            return Response({
                "status": False,
                "message": "Notification not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_notification(request.user, notification):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        updated = NotificationService.mark_as_read(notification)
        data = NotificationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Notification marked as read.",
            "data": {"notification": data}
        })


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Notifications"],
        responses={200: UnreadCountResponseSerializer},
        description="Mark all notifications for the authenticated user as read."
    )
    @transaction.atomic
    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user.id)
        return Response({
            "status": True,
            "message": f"{count} notifications marked as read.",
            "data": {"unread_count": 0}
        })


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Notifications"],
        responses={200: UnreadCountResponseSerializer},
        description="Get the count of unread notifications for the authenticated user."
    )
    def get(self, request):
        count = NotificationService.get_unread_count(request.user.id)
        return Response({
            "status": True,
            "message": "Unread count retrieved.",
            "data": {"unread_count": count}
        })