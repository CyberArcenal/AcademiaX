import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from alumni.models import AlumniEvent, EventAttendance
from alumni.serializers.event import (
    AlumniEventMinimalSerializer,
    AlumniEventCreateSerializer,
    AlumniEventUpdateSerializer,
    AlumniEventDisplaySerializer,
    EventAttendanceMinimalSerializer,
    EventAttendanceCreateSerializer,
    EventAttendanceUpdateSerializer,
    EventAttendanceDisplaySerializer,
)
from alumni.services.event import AlumniEventService, EventAttendanceService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers for AlumniEvent
# ----------------------------------------------------------------------

class AlumniEventCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()

class AlumniEventCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniEventCreateResponseData(allow_null=True)

class AlumniEventUpdateResponseData(serializers.Serializer):
    event = AlumniEventDisplaySerializer()

class AlumniEventUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniEventUpdateResponseData(allow_null=True)

class AlumniEventDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AlumniEventDetailResponseData(serializers.Serializer):
    event = AlumniEventDisplaySerializer()

class AlumniEventDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniEventDetailResponseData(allow_null=True)

class AlumniEventListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AlumniEventMinimalSerializer(many=True)

class AlumniEventListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniEventListResponseData()

# ----------------------------------------------------------------------
# Response serializers for EventAttendance
# ----------------------------------------------------------------------

class EventAttendanceCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    alumni = serializers.IntegerField()
    event = serializers.IntegerField()

class EventAttendanceCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EventAttendanceCreateResponseData(allow_null=True)

class EventAttendanceUpdateResponseData(serializers.Serializer):
    attendance = EventAttendanceDisplaySerializer()

class EventAttendanceUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EventAttendanceUpdateResponseData(allow_null=True)

class EventAttendanceDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EventAttendanceDetailResponseData(serializers.Serializer):
    attendance = EventAttendanceDisplaySerializer()

class EventAttendanceDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EventAttendanceDetailResponseData(allow_null=True)

class EventAttendanceListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EventAttendanceMinimalSerializer(many=True)

class EventAttendanceListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EventAttendanceListResponseData()

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
# AlumniEvent Views
# ----------------------------------------------------------------------

class AlumniEventListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni - Events"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="upcoming", type=bool, description="Show only upcoming events", required=False),
        ],
        responses={200: AlumniEventListResponseSerializer},
        description="List alumni events (upcoming or all)."
    )
    def get(self, request):
        upcoming = request.query_params.get("upcoming", "false").lower() == "true"
        if upcoming:
            events = AlumniEventService.get_upcoming_events()
        else:
            events = AlumniEvent.objects.all().order_by('-event_date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(events, request)
        data = wrap_paginated_data(paginator, page, request, AlumniEventMinimalSerializer)
        return Response({
            "status": True,
            "message": "Events retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Alumni - Events"],
        request=AlumniEventCreateSerializer,
        responses={201: AlumniEventCreateResponseSerializer, 400: AlumniEventCreateResponseSerializer},
        description="Create a new alumni event."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = AlumniEventCreateSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save()
            return Response({
                "status": True,
                "message": "Event created.",
                "data": {"id": event.id, "title": event.title}
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AlumniEventDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, event_id):
        return AlumniEventService.get_event_by_id(event_id)

    @extend_schema(
        tags=["Alumni - Events"],
        responses={200: AlumniEventDetailResponseSerializer, 404: AlumniEventDetailResponseSerializer},
        description="Retrieve a single event by ID."
    )
    def get(self, request, event_id):
        event = self.get_object(event_id)
        if not event:
            return Response({
                "status": False,
                "message": "Event not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = AlumniEventDisplaySerializer(event, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Event retrieved.",
            "data": {"event": data}
        })

    @extend_schema(
        tags=["Alumni - Events"],
        request=AlumniEventUpdateSerializer,
        responses={200: AlumniEventUpdateResponseSerializer, 400: AlumniEventUpdateResponseSerializer, 403: AlumniEventUpdateResponseSerializer},
        description="Update an event (admin only)."
    )
    @transaction.atomic
    def put(self, request, event_id):
        return self._update(request, event_id, partial=False)

    @extend_schema(
        tags=["Alumni - Events"],
        request=AlumniEventUpdateSerializer,
        responses={200: AlumniEventUpdateResponseSerializer, 400: AlumniEventUpdateResponseSerializer, 403: AlumniEventUpdateResponseSerializer},
        description="Partially update an event (admin only)."
    )
    @transaction.atomic
    def patch(self, request, event_id):
        return self._update(request, event_id, partial=True)

    def _update(self, request, event_id, partial):
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        event = self.get_object(event_id)
        if not event:
            return Response({
                "status": False,
                "message": "Event not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = AlumniEventUpdateSerializer(event, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AlumniEventDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Event updated.",
                "data": {"event": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Alumni - Events"],
        responses={200: AlumniEventDeleteResponseSerializer, 403: AlumniEventDeleteResponseSerializer, 404: AlumniEventDeleteResponseSerializer},
        description="Delete an event (admin only)."
    )
    @transaction.atomic
    def delete(self, request, event_id):
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        event = self.get_object(event_id)
        if not event:
            return Response({
                "status": False,
                "message": "Event not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = AlumniEventService.delete_event(event)
        if success:
            return Response({
                "status": True,
                "message": "Event deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete event.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ----------------------------------------------------------------------
# EventAttendance Views
# ----------------------------------------------------------------------

class EventAttendanceListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni - Event Attendance"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="event_id", type=int, description="Filter by event ID", required=False),
            OpenApiParameter(name="alumni_id", type=int, description="Filter by alumni ID", required=False),
        ],
        responses={200: EventAttendanceListResponseSerializer},
        description="List event attendances, optionally filtered by event or alumni."
    )
    def get(self, request):
        event_id = request.query_params.get("event_id")
        alumni_id = request.query_params.get("alumni_id")
        if event_id:
            attendances = EventAttendanceService.get_attendances_by_event(event_id)
        elif alumni_id:
            attendances = EventAttendanceService.get_attendances_by_alumni(alumni_id)
        else:
            attendances = EventAttendance.objects.all().select_related('alumni', 'event').order_by('-event__event_date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(attendances, request)
        data = wrap_paginated_data(paginator, page, request, EventAttendanceMinimalSerializer)
        return Response({
            "status": True,
            "message": "Event attendances retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Alumni - Event Attendance"],
        request=EventAttendanceCreateSerializer,
        responses={201: EventAttendanceCreateResponseSerializer, 400: EventAttendanceCreateResponseSerializer},
        description="Create an event attendance (RSVP)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = EventAttendanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            attendance = serializer.save()
            return Response({
                "status": True,
                "message": "Attendance created.",
                "data": {
                    "id": attendance.id,
                    "alumni": attendance.alumni.id,
                    "event": attendance.event.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EventAttendanceDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, attendance_id):
        return EventAttendanceService.get_attendance_by_id(attendance_id)

    @extend_schema(
        tags=["Alumni - Event Attendance"],
        responses={200: EventAttendanceDetailResponseSerializer, 404: EventAttendanceDetailResponseSerializer},
        description="Retrieve a single event attendance by ID."
    )
    def get(self, request, attendance_id):
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = EventAttendanceDisplaySerializer(attendance, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Attendance retrieved.",
            "data": {"attendance": data}
        })

    @extend_schema(
        tags=["Alumni - Event Attendance"],
        request=EventAttendanceUpdateSerializer,
        responses={200: EventAttendanceUpdateResponseSerializer, 400: EventAttendanceUpdateResponseSerializer, 403: EventAttendanceUpdateResponseSerializer},
        description="Update an event attendance (RSVP status, attended)."
    )
    @transaction.atomic
    def put(self, request, attendance_id):
        return self._update(request, attendance_id, partial=False)

    @extend_schema(
        tags=["Alumni - Event Attendance"],
        request=EventAttendanceUpdateSerializer,
        responses={200: EventAttendanceUpdateResponseSerializer, 400: EventAttendanceUpdateResponseSerializer, 403: EventAttendanceUpdateResponseSerializer},
        description="Partially update an event attendance."
    )
    @transaction.atomic
    def patch(self, request, attendance_id):
        return self._update(request, attendance_id, partial=True)

    def _update(self, request, attendance_id, partial):
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Allow staff or the alumni owner
        if not (user.is_staff or (attendance.alumni.user and user == attendance.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = EventAttendanceUpdateSerializer(attendance, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EventAttendanceDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Attendance updated.",
                "data": {"attendance": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Alumni - Event Attendance"],
        responses={200: EventAttendanceDeleteResponseSerializer, 403: EventAttendanceDeleteResponseSerializer, 404: EventAttendanceDeleteResponseSerializer},
        description="Delete an event attendance."
    )
    @transaction.atomic
    def delete(self, request, attendance_id):
        attendance = self.get_object(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not (user.is_staff or (attendance.alumni.user and user == attendance.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = EventAttendanceService.delete_attendance(attendance)
        if success:
            return Response({
                "status": True,
                "message": "Attendance deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete attendance.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EventAttendanceCheckinView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Alumni - Event Attendance"],
        responses={200: EventAttendanceUpdateResponseSerializer, 404: EventAttendanceUpdateResponseSerializer},
        description="Mark an alumni as checked in at an event (staff only)."
    )
    @transaction.atomic
    def post(self, request, attendance_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Staff permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        attendance = EventAttendanceService.get_attendance_by_id(attendance_id)
        if not attendance:
            return Response({
                "status": False,
                "message": "Attendance not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = EventAttendanceService.mark_attended(attendance)
        data = EventAttendanceDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Checked in.",
            "data": {"attendance": data}
        })