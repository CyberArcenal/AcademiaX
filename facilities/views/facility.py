import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from facilities.models import Facility
from facilities.serializers.facility import (
    FacilityMinimalSerializer,
    FacilityCreateSerializer,
    FacilityUpdateSerializer,
    FacilityDisplaySerializer,
)
from facilities.services.facility import FacilityService

logger = logging.getLogger(__name__)

def can_manage_facility(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class FacilityCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    building = serializers.IntegerField()

class FacilityCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FacilityCreateResponseData(allow_null=True)

class FacilityUpdateResponseData(serializers.Serializer):
    facility = FacilityDisplaySerializer()

class FacilityUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FacilityUpdateResponseData(allow_null=True)

class FacilityDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class FacilityDetailResponseData(serializers.Serializer):
    facility = FacilityDisplaySerializer()

class FacilityDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FacilityDetailResponseData(allow_null=True)

class FacilityListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = FacilityMinimalSerializer(many=True)

class FacilityListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FacilityListResponseData()

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

class FacilityListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Facilities - Facilities"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="building_id", type=int, description="Filter by building ID", required=False),
            OpenApiParameter(name="facility_type", type=str, description="Filter by facility type", required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: FacilityListResponseSerializer},
        description="List facilities, optionally filtered by building or type."
    )
    def get(self, request):
        building_id = request.query_params.get("building_id")
        facility_type = request.query_params.get("facility_type")
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if building_id:
            facilities = FacilityService.get_facilities_by_building(building_id, active_only=active_only)
        elif facility_type:
            facilities = FacilityService.get_facilities_by_type(facility_type, active_only=active_only)
        else:
            facilities = Facility.objects.all()
            if active_only:
                facilities = facilities.filter(is_active=True)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(facilities, request)
        data = wrap_paginated_data(paginator, page, request, FacilityMinimalSerializer)
        return Response({
            "status": True,
            "message": "Facilities retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Facilities - Facilities"],
        request=FacilityCreateSerializer,
        responses={201: FacilityCreateResponseSerializer, 400: FacilityCreateResponseSerializer, 403: FacilityCreateResponseSerializer},
        description="Create a new facility (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_facility(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = FacilityCreateSerializer(data=request.data)
        if serializer.is_valid():
            facility = serializer.save()
            return Response({
                "status": True,
                "message": "Facility created.",
                "data": {
                    "id": facility.id,
                    "name": facility.name,
                    "building": facility.building.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FacilityDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, facility_id):
        return FacilityService.get_facility_by_id(facility_id)

    @extend_schema(
        tags=["Facilities - Facilities"],
        responses={200: FacilityDetailResponseSerializer, 404: FacilityDetailResponseSerializer},
        description="Retrieve a single facility by ID."
    )
    def get(self, request, facility_id):
        facility = self.get_object(facility_id)
        if not facility:
            return Response({
                "status": False,
                "message": "Facility not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = FacilityDisplaySerializer(facility, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Facility retrieved.",
            "data": {"facility": data}
        })

    @extend_schema(
        tags=["Facilities - Facilities"],
        request=FacilityUpdateSerializer,
        responses={200: FacilityUpdateResponseSerializer, 400: FacilityUpdateResponseSerializer, 403: FacilityUpdateResponseSerializer},
        description="Update a facility (admin only)."
    )
    @transaction.atomic
    def put(self, request, facility_id):
        return self._update(request, facility_id, partial=False)

    @extend_schema(
        tags=["Facilities - Facilities"],
        request=FacilityUpdateSerializer,
        responses={200: FacilityUpdateResponseSerializer, 400: FacilityUpdateResponseSerializer, 403: FacilityUpdateResponseSerializer},
        description="Partially update a facility."
    )
    @transaction.atomic
    def patch(self, request, facility_id):
        return self._update(request, facility_id, partial=True)

    def _update(self, request, facility_id, partial):
        if not can_manage_facility(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        facility = self.get_object(facility_id)
        if not facility:
            return Response({
                "status": False,
                "message": "Facility not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = FacilityUpdateSerializer(facility, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = FacilityDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Facility updated.",
                "data": {"facility": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Facilities - Facilities"],
        responses={200: FacilityDeleteResponseSerializer, 403: FacilityDeleteResponseSerializer, 404: FacilityDeleteResponseSerializer},
        description="Delete a facility (admin only)."
    )
    @transaction.atomic
    def delete(self, request, facility_id):
        if not can_manage_facility(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        facility = self.get_object(facility_id)
        if not facility:
            return Response({
                "status": False,
                "message": "Facility not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = FacilityService.delete_facility(facility)
        if success:
            return Response({
                "status": True,
                "message": "Facility deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete facility.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FacilityAvailableView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Facilities - Facilities"],
        parameters=[
            OpenApiParameter(name="facility_type", type=str, description="Filter by facility type", required=False),
        ],
        responses={200: serializers.Serializer},
        description="Get all available facilities (status = AVAILABLE)."
    )
    def get(self, request):
        facility_type = request.query_params.get("facility_type")
        available = FacilityService.get_available_facilities(facility_type)
        data = [
            {
                "id": f.id,
                "name": f.name,
                "building": f.building.name,
                "facility_type": f.get_facility_type_display(),
                "capacity": f.capacity,
            }
            for f in available
        ]
        return Response({
            "status": True,
            "message": "Available facilities retrieved.",
            "data": data
        })