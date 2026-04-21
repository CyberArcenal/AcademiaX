import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from timetable.models import ScheduleOverride
from timetable.serializers.schedule_override import (
    ScheduleOverrideMinimalSerializer,
    ScheduleOverrideCreateSerializer,
    ScheduleOverrideUpdateSerializer,
    ScheduleOverrideDisplaySerializer,
)
from timetable.services.schedule_override import ScheduleOverrideService
from timetable.services.schedule import ScheduleService

logger = logging.getLogger(__name__)

def can_manage_override(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class OverrideCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    schedule = serializers.IntegerField()
    date = serializers.DateField()
    is_cancelled = serializers.BooleanField()

class OverrideCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OverrideCreateResponseData(allow_null=True)

class OverrideUpdateResponseData(serializers.Serializer):
    override = ScheduleOverrideDisplaySerializer()

class OverrideUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OverrideUpdateResponseData(allow_null=True)

class OverrideDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class OverrideDetailResponseData(serializers.Serializer):
    override = ScheduleOverrideDisplaySerializer()

class OverrideDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OverrideDetailResponseData(allow_null=True)

class OverrideListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ScheduleOverrideMinimalSerializer(many=True)

class OverrideListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OverrideListResponseData()

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

class ScheduleOverrideListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Timetable - Overrides"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="schedule_id", type=int, description="Filter by schedule ID", required=False),
            OpenApiParameter(name="date", type=str, description="Filter by date (YYYY-MM-DD)", required=False),
        ],
        responses={200: OverrideListResponseSerializer},
        description="List schedule overrides (admin/registrar only)."
    )
    def get(self, request):
        if not can_manage_override(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        schedule_id = request.query_params.get("schedule_id")
        date_str = request.query_params.get("date")
        queryset = ScheduleOverride.objects.all().select_related('schedule', 'new_room', 'new_teacher')
        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        if date_str:
            from datetime import datetime
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(date=date)
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Invalid date format. Use YYYY-MM-DD.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ScheduleOverrideMinimalSerializer)
        return Response({
            "status": True,
            "message": "Schedule overrides retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Timetable - Overrides"],
        request=ScheduleOverrideCreateSerializer,
        responses={201: OverrideCreateResponseSerializer, 400: OverrideCreateResponseSerializer, 403: OverrideCreateResponseSerializer},
        description="Create a schedule override (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_override(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = ScheduleOverrideCreateSerializer(data=request.data)
        if serializer.is_valid():
            override = serializer.save()
            return Response({
                "status": True,
                "message": "Schedule override created.",
                "data": {
                    "id": override.id,
                    "schedule": override.schedule.id,
                    "date": override.date,
                    "is_cancelled": override.is_cancelled,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ScheduleOverrideDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, override_id):
        try:
            return ScheduleOverride.objects.select_related('schedule', 'new_room', 'new_teacher').get(id=override_id)
        except ScheduleOverride.DoesNotExist:
            return None

    @extend_schema(
        tags=["Timetable - Overrides"],
        responses={200: OverrideDetailResponseSerializer, 404: OverrideDetailResponseSerializer, 403: OverrideDetailResponseSerializer},
        description="Retrieve a single schedule override by ID."
    )
    def get(self, request, override_id):
        if not can_manage_override(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        override = self.get_object(override_id)
        if not override:
            return Response({
                "status": False,
                "message": "Override not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = ScheduleOverrideDisplaySerializer(override, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Override retrieved.",
            "data": {"override": data}
        })

    @extend_schema(
        tags=["Timetable - Overrides"],
        request=ScheduleOverrideUpdateSerializer,
        responses={200: OverrideUpdateResponseSerializer, 400: OverrideUpdateResponseSerializer, 403: OverrideUpdateResponseSerializer},
        description="Update a schedule override (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, override_id):
        return self._update(request, override_id, partial=False)

    @extend_schema(
        tags=["Timetable - Overrides"],
        request=ScheduleOverrideUpdateSerializer,
        responses={200: OverrideUpdateResponseSerializer, 400: OverrideUpdateResponseSerializer, 403: OverrideUpdateResponseSerializer},
        description="Partially update a schedule override."
    )
    @transaction.atomic
    def patch(self, request, override_id):
        return self._update(request, override_id, partial=True)

    def _update(self, request, override_id, partial):
        if not can_manage_override(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        override = self.get_object(override_id)
        if not override:
            return Response({
                "status": False,
                "message": "Override not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ScheduleOverrideUpdateSerializer(override, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ScheduleOverrideDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Override updated.",
                "data": {"override": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Timetable - Overrides"],
        responses={200: OverrideDeleteResponseSerializer, 403: OverrideDeleteResponseSerializer, 404: OverrideDeleteResponseSerializer},
        description="Delete a schedule override (admin only)."
    )
    @transaction.atomic
    def delete(self, request, override_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        override = self.get_object(override_id)
        if not override:
            return Response({
                "status": False,
                "message": "Override not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ScheduleOverrideService.delete_override(override)
        if success:
            return Response({
                "status": True,
                "message": "Override deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete override.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScheduleOverrideCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Timetable - Overrides"],
        responses={200: OverrideUpdateResponseSerializer, 403: OverrideUpdateResponseSerializer, 404: OverrideUpdateResponseSerializer},
        description="Cancel a schedule override (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request, override_id):
        if not can_manage_override(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        override = ScheduleOverrideService.get_override_by_id(override_id)
        if not override:
            return Response({
                "status": False,
                "message": "Override not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if override.is_cancelled:
            return Response({
                "status": False,
                "message": "Override already cancelled.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = ScheduleOverrideService.cancel_override(override)
        data = ScheduleOverrideDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Override cancelled.",
            "data": {"override": data}
        })