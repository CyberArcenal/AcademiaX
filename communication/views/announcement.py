import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from communication.models import Announcement
from communication.serializers.announcement import (
    AnnouncementMinimalSerializer,
    AnnouncementCreateSerializer,
    AnnouncementUpdateSerializer,
    AnnouncementDisplaySerializer,
)
from communication.services.announcement import AnnouncementService

logger = logging.getLogger(__name__)

def can_manage_announcement(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'PRINCIPAL'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AnnouncementCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    target_audience = serializers.CharField()

class AnnouncementCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnnouncementCreateResponseData(allow_null=True)

class AnnouncementUpdateResponseData(serializers.Serializer):
    announcement = AnnouncementDisplaySerializer()

class AnnouncementUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnnouncementUpdateResponseData(allow_null=True)

class AnnouncementDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AnnouncementDetailResponseData(serializers.Serializer):
    announcement = AnnouncementDisplaySerializer()

class AnnouncementDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnnouncementDetailResponseData(allow_null=True)

class AnnouncementListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AnnouncementMinimalSerializer(many=True)

class AnnouncementListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnnouncementListResponseData()

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

class AnnouncementListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Communication - Announcements"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: AnnouncementListResponseSerializer},
        description="List published announcements (public)."
    )
    def get(self, request):
        announcements = AnnouncementService.get_published_announcements()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(announcements, request)
        data = wrap_paginated_data(paginator, page, request, AnnouncementMinimalSerializer)
        return Response({
            "status": True,
            "message": "Announcements retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Communication - Announcements"],
        request=AnnouncementCreateSerializer,
        responses={201: AnnouncementCreateResponseSerializer, 400: AnnouncementCreateResponseSerializer, 403: AnnouncementCreateResponseSerializer},
        description="Create a new announcement (admin/principal only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_announcement(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = AnnouncementCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            announcement = serializer.save()
            return Response({
                "status": True,
                "message": "Announcement created.",
                "data": {
                    "id": announcement.id,
                    "title": announcement.title,
                    "target_audience": announcement.target_audience,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AnnouncementDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, announcement_id):
        return AnnouncementService.get_announcement_by_id(announcement_id)

    @extend_schema(
        tags=["Communication - Announcements"],
        responses={200: AnnouncementDetailResponseSerializer, 404: AnnouncementDetailResponseSerializer},
        description="Retrieve a single announcement by ID."
    )
    def get(self, request, announcement_id):
        announcement = self.get_object(announcement_id)
        if not announcement:
            return Response({
                "status": False,
                "message": "Announcement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = AnnouncementDisplaySerializer(announcement, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Announcement retrieved.",
            "data": {"announcement": data}
        })

    @extend_schema(
        tags=["Communication - Announcements"],
        request=AnnouncementUpdateSerializer,
        responses={200: AnnouncementUpdateResponseSerializer, 400: AnnouncementUpdateResponseSerializer, 403: AnnouncementUpdateResponseSerializer},
        description="Update an announcement (admin/principal only)."
    )
    @transaction.atomic
    def put(self, request, announcement_id):
        return self._update(request, announcement_id, partial=False)

    @extend_schema(
        tags=["Communication - Announcements"],
        request=AnnouncementUpdateSerializer,
        responses={200: AnnouncementUpdateResponseSerializer, 400: AnnouncementUpdateResponseSerializer, 403: AnnouncementUpdateResponseSerializer},
        description="Partially update an announcement."
    )
    @transaction.atomic
    def patch(self, request, announcement_id):
        return self._update(request, announcement_id, partial=True)

    def _update(self, request, announcement_id, partial):
        if not can_manage_announcement(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        announcement = self.get_object(announcement_id)
        if not announcement:
            return Response({
                "status": False,
                "message": "Announcement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = AnnouncementUpdateSerializer(announcement, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AnnouncementDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Announcement updated.",
                "data": {"announcement": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Communication - Announcements"],
        responses={200: AnnouncementDeleteResponseSerializer, 403: AnnouncementDeleteResponseSerializer, 404: AnnouncementDeleteResponseSerializer},
        description="Delete an announcement (admin/principal only)."
    )
    @transaction.atomic
    def delete(self, request, announcement_id):
        if not can_manage_announcement(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        announcement = self.get_object(announcement_id)
        if not announcement:
            return Response({
                "status": False,
                "message": "Announcement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = AnnouncementService.delete_announcement(announcement)
        if success:
            return Response({
                "status": True,
                "message": "Announcement deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete announcement.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnnouncementPublishView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Announcements"],
        responses={200: AnnouncementDetailResponseSerializer, 403: AnnouncementDetailResponseSerializer, 404: AnnouncementDetailResponseSerializer},
        description="Publish an announcement (admin/principal only)."
    )
    @transaction.atomic
    def post(self, request, announcement_id):
        if not can_manage_announcement(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        announcement = AnnouncementService.get_announcement_by_id(announcement_id)
        if not announcement:
            return Response({
                "status": False,
                "message": "Announcement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = AnnouncementService.publish_announcement(announcement)
        data = AnnouncementDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Announcement published.",
            "data": {"announcement": data}
        })