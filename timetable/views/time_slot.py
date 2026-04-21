import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from timetable.models import TimeSlot
from timetable.serializers.time_slot import (
    TimeSlotMinimalSerializer,
    TimeSlotCreateSerializer,
    TimeSlotUpdateSerializer,
    TimeSlotDisplaySerializer,
)
from timetable.services.time_slot import TimeSlotService

logger = logging.getLogger(__name__)

def can_manage_time_slot(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TimeSlotCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    day_of_week = serializers.CharField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

class TimeSlotCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TimeSlotCreateResponseData(allow_null=True)

class TimeSlotUpdateResponseData(serializers.Serializer):
    time_slot = TimeSlotDisplaySerializer()

class TimeSlotUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TimeSlotUpdateResponseData(allow_null=True)

class TimeSlotDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TimeSlotDetailResponseData(serializers.Serializer):
    time_slot = TimeSlotDisplaySerializer()

class TimeSlotDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TimeSlotDetailResponseData(allow_null=True)

class TimeSlotListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TimeSlotMinimalSerializer(many=True)

class TimeSlotListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TimeSlotListResponseData()

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

class TimeSlotListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Timetable - Time Slots"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year", required=False),
        ],
        responses={200: TimeSlotListResponseSerializer},
        description="List time slots (admin only)."
    )
    def get(self, request):
        if not can_manage_time_slot(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        academic_year_id = request.query_params.get("academic_year_id")
        if academic_year_id:
            slots = TimeSlotService.get_time_slots_by_academic_year(academic_year_id)
        else:
            slots = TimeSlot.objects.all().order_by('academic_year', 'day_of_week', 'order')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(slots, request)
        data = wrap_paginated_data(paginator, page, request, TimeSlotMinimalSerializer)
        return Response({
            "status": True,
            "message": "Time slots retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Timetable - Time Slots"],
        request=TimeSlotCreateSerializer,
        responses={201: TimeSlotCreateResponseSerializer, 400: TimeSlotCreateResponseSerializer, 403: TimeSlotCreateResponseSerializer},
        description="Create a time slot (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_time_slot(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = TimeSlotCreateSerializer(data=request.data)
        if serializer.is_valid():
            slot = serializer.save()
            return Response({
                "status": True,
                "message": "Time slot created.",
                "data": {
                    "id": slot.id,
                    "name": slot.name,
                    "day_of_week": slot.day_of_week,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TimeSlotDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, slot_id):
        try:
            return TimeSlot.objects.get(id=slot_id)
        except TimeSlot.DoesNotExist:
            return None

    @extend_schema(
        tags=["Timetable - Time Slots"],
        responses={200: TimeSlotDetailResponseSerializer, 404: TimeSlotDetailResponseSerializer, 403: TimeSlotDetailResponseSerializer},
        description="Retrieve a single time slot by ID."
    )
    def get(self, request, slot_id):
        if not can_manage_time_slot(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        slot = self.get_object(slot_id)
        if not slot:
            return Response({
                "status": False,
                "message": "Time slot not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = TimeSlotDisplaySerializer(slot, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Time slot retrieved.",
            "data": {"time_slot": data}
        })

    @extend_schema(
        tags=["Timetable - Time Slots"],
        request=TimeSlotUpdateSerializer,
        responses={200: TimeSlotUpdateResponseSerializer, 400: TimeSlotUpdateResponseSerializer, 403: TimeSlotUpdateResponseSerializer},
        description="Update a time slot (admin only)."
    )
    @transaction.atomic
    def put(self, request, slot_id):
        return self._update(request, slot_id, partial=False)

    @extend_schema(
        tags=["Timetable - Time Slots"],
        request=TimeSlotUpdateSerializer,
        responses={200: TimeSlotUpdateResponseSerializer, 400: TimeSlotUpdateResponseSerializer, 403: TimeSlotUpdateResponseSerializer},
        description="Partially update a time slot."
    )
    @transaction.atomic
    def patch(self, request, slot_id):
        return self._update(request, slot_id, partial=True)

    def _update(self, request, slot_id, partial):
        if not can_manage_time_slot(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        slot = self.get_object(slot_id)
        if not slot:
            return Response({
                "status": False,
                "message": "Time slot not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TimeSlotUpdateSerializer(slot, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = TimeSlotDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Time slot updated.",
                "data": {"time_slot": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Timetable - Time Slots"],
        responses={200: TimeSlotDeleteResponseSerializer, 403: TimeSlotDeleteResponseSerializer, 404: TimeSlotDeleteResponseSerializer},
        description="Delete a time slot (admin only)."
    )
    @transaction.atomic
    def delete(self, request, slot_id):
        if not can_manage_time_slot(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        slot = self.get_object(slot_id)
        if not slot:
            return Response({
                "status": False,
                "message": "Time slot not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = TimeSlotService.delete_time_slot(slot)
        if success:
            return Response({
                "status": True,
                "message": "Time slot deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete time slot.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TimeSlotReorderView(APIView):
    permission_classes = [IsAuthenticated]

    class ReorderSerializer(serializers.Serializer):
        slot_ids = serializers.ListField(child=serializers.IntegerField())

    @extend_schema(
        tags=["Timetable - Time Slots"],
        request=ReorderSerializer,
        responses={200: serializers.Serializer, 400: serializers.Serializer, 403: serializers.Serializer},
        description="Reorder time slots for an academic year (admin only)."
    )
    @transaction.atomic
    def post(self, request, academic_year_id):
        if not can_manage_time_slot(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        success = TimeSlotService.reorder_time_slots(academic_year_id, serializer.validated_data['slot_ids'])
        if success:
            return Response({
                "status": True,
                "message": "Time slots reordered.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Reorder failed.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)