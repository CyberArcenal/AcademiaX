import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from hr.models import Position
from hr.serializers.position import (
    PositionMinimalSerializer,
    PositionCreateSerializer,
    PositionUpdateSerializer,
    PositionDisplaySerializer,
)
from hr.services.position import PositionService

logger = logging.getLogger(__name__)

def can_manage_position(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class PositionCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    department = serializers.IntegerField()

class PositionCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PositionCreateResponseData(allow_null=True)

class PositionUpdateResponseData(serializers.Serializer):
    position = PositionDisplaySerializer()

class PositionUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PositionUpdateResponseData(allow_null=True)

class PositionDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class PositionDetailResponseData(serializers.Serializer):
    position = PositionDisplaySerializer()

class PositionDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PositionDetailResponseData(allow_null=True)

class PositionListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PositionMinimalSerializer(many=True)

class PositionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PositionListResponseData()

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

class PositionListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["HR - Positions"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="department_id", type=int, description="Filter by department ID", required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: PositionListResponseSerializer},
        description="List positions, optionally filtered by department."
    )
    def get(self, request):
        department_id = request.query_params.get("department_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if department_id:
            positions = PositionService.get_positions_by_department(department_id, active_only=active_only)
        else:
            queryset = Position.objects.all()
            if active_only:
                queryset = queryset.filter(is_active=True)
            positions = queryset.select_related('department')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(positions, request)
        data = wrap_paginated_data(paginator, page, request, PositionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Positions retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Positions"],
        request=PositionCreateSerializer,
        responses={201: PositionCreateResponseSerializer, 400: PositionCreateResponseSerializer, 403: PositionCreateResponseSerializer},
        description="Create a new position (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_position(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = PositionCreateSerializer(data=request.data)
        if serializer.is_valid():
            position = serializer.save()
            return Response({
                "status": True,
                "message": "Position created.",
                "data": {
                    "id": position.id,
                    "title": position.title,
                    "department": position.department.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PositionDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, position_id):
        try:
            return Position.objects.select_related('department').get(id=position_id)
        except Position.DoesNotExist:
            return None

    @extend_schema(
        tags=["HR - Positions"],
        responses={200: PositionDetailResponseSerializer, 404: PositionDetailResponseSerializer},
        description="Retrieve a single position by ID."
    )
    def get(self, request, position_id):
        position = self.get_object(position_id)
        if not position:
            return Response({
                "status": False,
                "message": "Position not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = PositionDisplaySerializer(position, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Position retrieved.",
            "data": {"position": data}
        })

    @extend_schema(
        tags=["HR - Positions"],
        request=PositionUpdateSerializer,
        responses={200: PositionUpdateResponseSerializer, 400: PositionUpdateResponseSerializer, 403: PositionUpdateResponseSerializer},
        description="Update a position (admin/hr only)."
    )
    @transaction.atomic
    def put(self, request, position_id):
        return self._update(request, position_id, partial=False)

    @extend_schema(
        tags=["HR - Positions"],
        request=PositionUpdateSerializer,
        responses={200: PositionUpdateResponseSerializer, 400: PositionUpdateResponseSerializer, 403: PositionUpdateResponseSerializer},
        description="Partially update a position."
    )
    @transaction.atomic
    def patch(self, request, position_id):
        return self._update(request, position_id, partial=True)

    def _update(self, request, position_id, partial):
        if not can_manage_position(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        position = self.get_object(position_id)
        if not position:
            return Response({
                "status": False,
                "message": "Position not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = PositionUpdateSerializer(position, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PositionDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Position updated.",
                "data": {"position": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["HR - Positions"],
        responses={200: PositionDeleteResponseSerializer, 403: PositionDeleteResponseSerializer, 404: PositionDeleteResponseSerializer},
        description="Delete a position (admin/hr only)."
    )
    @transaction.atomic
    def delete(self, request, position_id):
        if not can_manage_position(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        position = self.get_object(position_id)
        if not position:
            return Response({
                "status": False,
                "message": "Position not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = PositionService.delete_position(position)
        if success:
            return Response({
                "status": True,
                "message": "Position deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete position.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)