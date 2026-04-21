import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from library.models import Publisher
from library.serializers.publisher import (
    PublisherMinimalSerializer,
    PublisherCreateSerializer,
    PublisherUpdateSerializer,
    PublisherDisplaySerializer,
)
from library.services.publisher import PublisherService

logger = logging.getLogger(__name__)

def can_manage_publisher(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class PublisherCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class PublisherCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PublisherCreateResponseData(allow_null=True)

class PublisherUpdateResponseData(serializers.Serializer):
    publisher = PublisherDisplaySerializer()

class PublisherUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PublisherUpdateResponseData(allow_null=True)

class PublisherDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class PublisherDetailResponseData(serializers.Serializer):
    publisher = PublisherDisplaySerializer()

class PublisherDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PublisherDetailResponseData(allow_null=True)

class PublisherListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PublisherMinimalSerializer(many=True)

class PublisherListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PublisherListResponseData()

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

class PublisherListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Library - Publishers"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: PublisherListResponseSerializer},
        description="List publishers (public)."
    )
    def get(self, request):
        publishers = PublisherService.get_all_publishers()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(publishers, request)
        data = wrap_paginated_data(paginator, page, request, PublisherMinimalSerializer)
        return Response({
            "status": True,
            "message": "Publishers retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Library - Publishers"],
        request=PublisherCreateSerializer,
        responses={201: PublisherCreateResponseSerializer, 400: PublisherCreateResponseSerializer, 403: PublisherCreateResponseSerializer},
        description="Create a new publisher (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_publisher(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = PublisherCreateSerializer(data=request.data)
        if serializer.is_valid():
            publisher = serializer.save()
            return Response({
                "status": True,
                "message": "Publisher created.",
                "data": {
                    "id": publisher.id,
                    "name": publisher.name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PublisherDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, publisher_id):
        return PublisherService.get_publisher_by_id(publisher_id)

    @extend_schema(
        tags=["Library - Publishers"],
        responses={200: PublisherDetailResponseSerializer, 404: PublisherDetailResponseSerializer},
        description="Retrieve a single publisher by ID."
    )
    def get(self, request, publisher_id):
        publisher = self.get_object(publisher_id)
        if not publisher:
            return Response({
                "status": False,
                "message": "Publisher not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = PublisherDisplaySerializer(publisher, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Publisher retrieved.",
            "data": {"publisher": data}
        })

    @extend_schema(
        tags=["Library - Publishers"],
        request=PublisherUpdateSerializer,
        responses={200: PublisherUpdateResponseSerializer, 400: PublisherUpdateResponseSerializer, 403: PublisherUpdateResponseSerializer},
        description="Update a publisher (admin only)."
    )
    @transaction.atomic
    def put(self, request, publisher_id):
        return self._update(request, publisher_id, partial=False)

    @extend_schema(
        tags=["Library - Publishers"],
        request=PublisherUpdateSerializer,
        responses={200: PublisherUpdateResponseSerializer, 400: PublisherUpdateResponseSerializer, 403: PublisherUpdateResponseSerializer},
        description="Partially update a publisher."
    )
    @transaction.atomic
    def patch(self, request, publisher_id):
        return self._update(request, publisher_id, partial=True)

    def _update(self, request, publisher_id, partial):
        if not can_manage_publisher(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        publisher = self.get_object(publisher_id)
        if not publisher:
            return Response({
                "status": False,
                "message": "Publisher not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = PublisherUpdateSerializer(publisher, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PublisherDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Publisher updated.",
                "data": {"publisher": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Library - Publishers"],
        responses={200: PublisherDeleteResponseSerializer, 403: PublisherDeleteResponseSerializer, 404: PublisherDeleteResponseSerializer},
        description="Delete a publisher (admin only)."
    )
    @transaction.atomic
    def delete(self, request, publisher_id):
        if not can_manage_publisher(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        publisher = self.get_object(publisher_id)
        if not publisher:
            return Response({
                "status": False,
                "message": "Publisher not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = PublisherService.delete_publisher(publisher)
        if success:
            return Response({
                "status": True,
                "message": "Publisher deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete publisher.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)