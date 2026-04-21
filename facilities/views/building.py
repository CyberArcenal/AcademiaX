import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from facilities.models import Building
from facilities.serializers.building import (
    BuildingMinimalSerializer,
    BuildingCreateSerializer,
    BuildingUpdateSerializer,
    BuildingDisplaySerializer,
)
from facilities.services.building import BuildingService

logger = logging.getLogger(__name__)

def can_manage_building(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class BuildingCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()

class BuildingCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BuildingCreateResponseData(allow_null=True)

class BuildingUpdateResponseData(serializers.Serializer):
    building = BuildingDisplaySerializer()

class BuildingUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BuildingUpdateResponseData(allow_null=True)

class BuildingDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class BuildingDetailResponseData(serializers.Serializer):
    building = BuildingDisplaySerializer()

class BuildingDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BuildingDetailResponseData(allow_null=True)

class BuildingListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = BuildingMinimalSerializer(many=True)

class BuildingListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BuildingListResponseData()

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

class BuildingListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Facilities - Buildings"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: BuildingListResponseSerializer},
        description="List buildings."
    )
    def get(self, request):
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        buildings = BuildingService.get_all_buildings(active_only=active_only)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(buildings, request)
        data = wrap_paginated_data(paginator, page, request, BuildingMinimalSerializer)
        return Response({
            "status": True,
            "message": "Buildings retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Facilities - Buildings"],
        request=BuildingCreateSerializer,
        responses={201: BuildingCreateResponseSerializer, 400: BuildingCreateResponseSerializer, 403: BuildingCreateResponseSerializer},
        description="Create a new building (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_building(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = BuildingCreateSerializer(data=request.data)
        if serializer.is_valid():
            building = serializer.save()
            return Response({
                "status": True,
                "message": "Building created.",
                "data": {
                    "id": building.id,
                    "name": building.name,
                    "code": building.code,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BuildingDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, building_id):
        return BuildingService.get_building_by_id(building_id)

    @extend_schema(
        tags=["Facilities - Buildings"],
        responses={200: BuildingDetailResponseSerializer, 404: BuildingDetailResponseSerializer},
        description="Retrieve a single building by ID."
    )
    def get(self, request, building_id):
        building = self.get_object(building_id)
        if not building:
            return Response({
                "status": False,
                "message": "Building not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = BuildingDisplaySerializer(building, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Building retrieved.",
            "data": {"building": data}
        })

    @extend_schema(
        tags=["Facilities - Buildings"],
        request=BuildingUpdateSerializer,
        responses={200: BuildingUpdateResponseSerializer, 400: BuildingUpdateResponseSerializer, 403: BuildingUpdateResponseSerializer},
        description="Update a building (admin only)."
    )
    @transaction.atomic
    def put(self, request, building_id):
        return self._update(request, building_id, partial=False)

    @extend_schema(
        tags=["Facilities - Buildings"],
        request=BuildingUpdateSerializer,
        responses={200: BuildingUpdateResponseSerializer, 400: BuildingUpdateResponseSerializer, 403: BuildingUpdateResponseSerializer},
        description="Partially update a building."
    )
    @transaction.atomic
    def patch(self, request, building_id):
        return self._update(request, building_id, partial=True)

    def _update(self, request, building_id, partial):
        if not can_manage_building(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        building = self.get_object(building_id)
        if not building:
            return Response({
                "status": False,
                "message": "Building not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = BuildingUpdateSerializer(building, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = BuildingDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Building updated.",
                "data": {"building": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Facilities - Buildings"],
        responses={200: BuildingDeleteResponseSerializer, 403: BuildingDeleteResponseSerializer, 404: BuildingDeleteResponseSerializer},
        description="Delete a building (admin only)."
    )
    @transaction.atomic
    def delete(self, request, building_id):
        if not can_manage_building(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        building = self.get_object(building_id)
        if not building:
            return Response({
                "status": False,
                "message": "Building not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = BuildingService.delete_building(building)
        if success:
            return Response({
                "status": True,
                "message": "Building deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete building.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)