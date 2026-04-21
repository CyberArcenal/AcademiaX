import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from timetable.models import RoomSchedule
from timetable.serializers.room_schedule import (
    RoomScheduleMinimalSerializer,
    RoomScheduleCreateSerializer,
    RoomScheduleUpdateSerializer,
    RoomScheduleDisplaySerializer,
)
from timetable.services.room_schedule import RoomScheduleService

logger = logging.getLogger(__name__)

def can_manage_room_schedule(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class RoomScheduleCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    room = serializers.IntegerField()
    time_slot = serializers.IntegerField()
    event_name = serializers.CharField()
    date = serializers.DateField()

class RoomScheduleCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = RoomScheduleCreateResponseData(allow_null=True)

class RoomScheduleUpdateResponseData(serializers.Serializer):
    room_schedule = RoomScheduleDisplaySerializer()

class RoomScheduleUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = RoomScheduleUpdateResponseData(allow_null=True)

class RoomScheduleDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class RoomScheduleDetailResponseData(serializers.Serializer):
    room_schedule = RoomScheduleDisplaySerializer()

class RoomScheduleDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = RoomScheduleDetailResponseData(allow_null=True)

class RoomScheduleListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = RoomScheduleMinimalSerializer(many=True)

class RoomScheduleListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = RoomScheduleListResponseData()

class RoomAvailabilityResponseData(serializers.Serializer):
    time_slot_id = serializers.IntegerField()
    name = serializers.CharField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

class RoomAvailabilityResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.ListField(child=RoomAvailabilityResponseData())

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

class RoomScheduleListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Timetable - Room Schedules"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="room_id", type=int, description="Filter by room ID", required=False),
            OpenApiParameter(name="date", type=str, description="Filter by date (YYYY-MM-DD)", required=False),
        ],
        responses={200: RoomScheduleListResponseSerializer},
        description="List room schedules (admin/registrar only)."
    )
    def get(self, request):
        if not can_manage_room_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        room_id = request.query_params.get("room_id")
        date_str = request.query_params.get("date")
        queryset = RoomSchedule.objects.all().select_related('room', 'time_slot')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
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
        queryset = queryset.order_by('date', 'time_slot__order')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, RoomScheduleMinimalSerializer)
        return Response({
            "status": True,
            "message": "Room schedules retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Timetable - Room Schedules"],
        request=RoomScheduleCreateSerializer,
        responses={201: RoomScheduleCreateResponseSerializer, 400: RoomScheduleCreateResponseSerializer, 403: RoomScheduleCreateResponseSerializer},
        description="Create a room schedule (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_room_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = RoomScheduleCreateSerializer(data=request.data)
        if serializer.is_valid():
            room_schedule = serializer.save()
            return Response({
                "status": True,
                "message": "Room schedule created.",
                "data": {
                    "id": room_schedule.id,
                    "room": room_schedule.room.id,
                    "time_slot": room_schedule.time_slot.id,
                    "event_name": room_schedule.event_name,
                    "date": room_schedule.date,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RoomScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, room_schedule_id):
        try:
            return RoomSchedule.objects.select_related('room', 'time_slot').get(id=room_schedule_id)
        except RoomSchedule.DoesNotExist:
            return None

    @extend_schema(
        tags=["Timetable - Room Schedules"],
        responses={200: RoomScheduleDetailResponseSerializer, 404: RoomScheduleDetailResponseSerializer, 403: RoomScheduleDetailResponseSerializer},
        description="Retrieve a single room schedule by ID."
    )
    def get(self, request, room_schedule_id):
        if not can_manage_room_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        room_schedule = self.get_object(room_schedule_id)
        if not room_schedule:
            return Response({
                "status": False,
                "message": "Room schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = RoomScheduleDisplaySerializer(room_schedule, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Room schedule retrieved.",
            "data": {"room_schedule": data}
        })

    @extend_schema(
        tags=["Timetable - Room Schedules"],
        request=RoomScheduleUpdateSerializer,
        responses={200: RoomScheduleUpdateResponseSerializer, 400: RoomScheduleUpdateResponseSerializer, 403: RoomScheduleUpdateResponseSerializer},
        description="Update a room schedule (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, room_schedule_id):
        return self._update(request, room_schedule_id, partial=False)

    @extend_schema(
        tags=["Timetable - Room Schedules"],
        request=RoomScheduleUpdateSerializer,
        responses={200: RoomScheduleUpdateResponseSerializer, 400: RoomScheduleUpdateResponseSerializer, 403: RoomScheduleUpdateResponseSerializer},
        description="Partially update a room schedule."
    )
    @transaction.atomic
    def patch(self, request, room_schedule_id):
        return self._update(request, room_schedule_id, partial=True)

    def _update(self, request, room_schedule_id, partial):
        if not can_manage_room_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        room_schedule = self.get_object(room_schedule_id)
        if not room_schedule:
            return Response({
                "status": False,
                "message": "Room schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = RoomScheduleUpdateSerializer(room_schedule, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = RoomScheduleDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Room schedule updated.",
                "data": {"room_schedule": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Timetable - Room Schedules"],
        responses={200: RoomScheduleDeleteResponseSerializer, 403: RoomScheduleDeleteResponseSerializer, 404: RoomScheduleDeleteResponseSerializer},
        description="Delete a room schedule (admin only)."
    )
    @transaction.atomic
    def delete(self, request, room_schedule_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        room_schedule = self.get_object(room_schedule_id)
        if not room_schedule:
            return Response({
                "status": False,
                "message": "Room schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = RoomScheduleService.delete_room_schedule(room_schedule)
        if success:
            return Response({
                "status": True,
                "message": "Room schedule deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete room schedule.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoomAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Timetable - Room Schedules"],
        parameters=[
            OpenApiParameter(name="room_id", type=int, description="Room ID", required=True),
            OpenApiParameter(name="date", type=str, description="Date (YYYY-MM-DD)", required=True),
        ],
        responses={200: RoomAvailabilityResponseSerializer, 400: RoomAvailabilityResponseSerializer, 403: RoomAvailabilityResponseSerializer},
        description="Get available time slots for a room on a given date."
    )
    def get(self, request):
        if not can_manage_room_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        room_id = request.query_params.get("room_id")
        date_str = request.query_params.get("date")
        if not room_id or not date_str:
            return Response({
                "status": False,
                "message": "room_id and date parameters required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        from datetime import datetime
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "status": False,
                "message": "Invalid date format. Use YYYY-MM-DD.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        available = RoomScheduleService.get_room_availability(room_id, date)
        return Response({
            "status": True,
            "message": "Room availability retrieved.",
            "data": available
        })