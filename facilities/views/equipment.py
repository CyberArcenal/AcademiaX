import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from facilities.models import Equipment
from facilities.serializers.equipment import (
    EquipmentMinimalSerializer,
    EquipmentCreateSerializer,
    EquipmentUpdateSerializer,
    EquipmentDisplaySerializer,
)
from facilities.services.equipment import EquipmentService

logger = logging.getLogger(__name__)

def can_manage_equipment(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class EquipmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    serial_number = serializers.CharField()

class EquipmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EquipmentCreateResponseData(allow_null=True)

class EquipmentUpdateResponseData(serializers.Serializer):
    equipment = EquipmentDisplaySerializer()

class EquipmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EquipmentUpdateResponseData(allow_null=True)

class EquipmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EquipmentDetailResponseData(serializers.Serializer):
    equipment = EquipmentDisplaySerializer()

class EquipmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EquipmentDetailResponseData(allow_null=True)

class EquipmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EquipmentMinimalSerializer(many=True)

class EquipmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EquipmentListResponseData()

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

class EquipmentListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Facilities - Equipment"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="facility_id", type=int, description="Filter by facility ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by equipment status", required=False),
        ],
        responses={200: EquipmentListResponseSerializer},
        description="List equipment, optionally filtered by facility or status."
    )
    def get(self, request):
        facility_id = request.query_params.get("facility_id")
        status_filter = request.query_params.get("status")
        if facility_id:
            equipment = EquipmentService.get_equipment_by_facility(facility_id)
        elif status_filter:
            equipment = EquipmentService.get_equipment_by_status(status_filter)
        else:
            equipment = Equipment.objects.all()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(equipment, request)
        data = wrap_paginated_data(paginator, page, request, EquipmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Equipment retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Facilities - Equipment"],
        request=EquipmentCreateSerializer,
        responses={201: EquipmentCreateResponseSerializer, 400: EquipmentCreateResponseSerializer, 403: EquipmentCreateResponseSerializer},
        description="Create new equipment (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_equipment(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = EquipmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            equipment = serializer.save()
            return Response({
                "status": True,
                "message": "Equipment created.",
                "data": {
                    "id": equipment.id,
                    "name": equipment.name,
                    "serial_number": equipment.serial_number,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EquipmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, equipment_id):
        return EquipmentService.get_equipment_by_id(equipment_id)

    @extend_schema(
        tags=["Facilities - Equipment"],
        responses={200: EquipmentDetailResponseSerializer, 404: EquipmentDetailResponseSerializer},
        description="Retrieve a single equipment item by ID."
    )
    def get(self, request, equipment_id):
        equipment = self.get_object(equipment_id)
        if not equipment:
            return Response({
                "status": False,
                "message": "Equipment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = EquipmentDisplaySerializer(equipment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Equipment retrieved.",
            "data": {"equipment": data}
        })

    @extend_schema(
        tags=["Facilities - Equipment"],
        request=EquipmentUpdateSerializer,
        responses={200: EquipmentUpdateResponseSerializer, 400: EquipmentUpdateResponseSerializer, 403: EquipmentUpdateResponseSerializer},
        description="Update equipment (admin only)."
    )
    @transaction.atomic
    def put(self, request, equipment_id):
        return self._update(request, equipment_id, partial=False)

    @extend_schema(
        tags=["Facilities - Equipment"],
        request=EquipmentUpdateSerializer,
        responses={200: EquipmentUpdateResponseSerializer, 400: EquipmentUpdateResponseSerializer, 403: EquipmentUpdateResponseSerializer},
        description="Partially update equipment."
    )
    @transaction.atomic
    def patch(self, request, equipment_id):
        return self._update(request, equipment_id, partial=True)

    def _update(self, request, equipment_id, partial):
        if not can_manage_equipment(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        equipment = self.get_object(equipment_id)
        if not equipment:
            return Response({
                "status": False,
                "message": "Equipment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = EquipmentUpdateSerializer(equipment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EquipmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Equipment updated.",
                "data": {"equipment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Facilities - Equipment"],
        responses={200: EquipmentDeleteResponseSerializer, 403: EquipmentDeleteResponseSerializer, 404: EquipmentDeleteResponseSerializer},
        description="Delete equipment (admin only)."
    )
    @transaction.atomic
    def delete(self, request, equipment_id):
        if not can_manage_equipment(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        equipment = self.get_object(equipment_id)
        if not equipment:
            return Response({
                "status": False,
                "message": "Equipment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = EquipmentService.delete_equipment(equipment)
        if success:
            return Response({
                "status": True,
                "message": "Equipment deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete equipment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EquipmentUpdateStatusView(APIView):
    permission_classes = [IsAuthenticated]

    class StatusSerializer(serializers.Serializer):
        status = serializers.CharField()

    @extend_schema(
        tags=["Facilities - Equipment"],
        request=StatusSerializer,
        responses={200: EquipmentUpdateResponseSerializer, 400: EquipmentUpdateResponseSerializer, 403: EquipmentUpdateResponseSerializer},
        description="Update equipment status (admin only)."
    )
    @transaction.atomic
    def post(self, request, equipment_id):
        if not can_manage_equipment(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        equipment = EquipmentService.get_equipment_by_id(equipment_id)
        if not equipment:
            return Response({
                "status": False,
                "message": "Equipment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.StatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = EquipmentService.update_equipment_status(equipment, serializer.validated_data['status'])
        data = EquipmentDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Equipment status updated.",
            "data": {"equipment": data}
        })