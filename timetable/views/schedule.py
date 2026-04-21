import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from timetable.models import Schedule
from timetable.serializers.schedule import (
    ScheduleMinimalSerializer,
    ScheduleCreateSerializer,
    ScheduleUpdateSerializer,
    ScheduleDisplaySerializer,
)
from timetable.services.schedule import ScheduleService

logger = logging.getLogger(__name__)

def can_view_schedule(user, schedule):
    if user.is_staff:
        return True
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        return schedule.teacher == user.teacher_profile
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return schedule.section.enrollments.filter(student=user.student_profile).exists()
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        child_ids = user.parent_profile.students.values_list('student_id', flat=True)
        return schedule.section.enrollments.filter(student_id__in=child_ids).exists()
    return False

def can_manage_schedule(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ScheduleCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    time_slot = serializers.IntegerField()
    section = serializers.IntegerField()
    subject = serializers.IntegerField()
    teacher = serializers.IntegerField()
    room = serializers.IntegerField()

class ScheduleCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScheduleCreateResponseData(allow_null=True)

class ScheduleUpdateResponseData(serializers.Serializer):
    schedule = ScheduleDisplaySerializer()

class ScheduleUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScheduleUpdateResponseData(allow_null=True)

class ScheduleDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ScheduleDetailResponseData(serializers.Serializer):
    schedule = ScheduleDisplaySerializer()

class ScheduleDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScheduleDetailResponseData(allow_null=True)

class ScheduleListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ScheduleMinimalSerializer(many=True)

class ScheduleListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScheduleListResponseData()

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

class ScheduleListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Timetable - Schedules"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="section_id", type=int, description="Filter by section ID", required=False),
            OpenApiParameter(name="teacher_id", type=int, description="Filter by teacher ID", required=False),
            OpenApiParameter(name="room_id", type=int, description="Filter by room ID", required=False),
            OpenApiParameter(name="term_id", type=int, description="Filter by term ID", required=False),
        ],
        responses={200: ScheduleListResponseSerializer},
        description="List schedules (filtered by role)."
    )
    def get(self, request):
        user = request.user
        section_id = request.query_params.get("section_id")
        teacher_id = request.query_params.get("teacher_id")
        room_id = request.query_params.get("room_id")
        term_id = request.query_params.get("term_id")

        if user.is_staff or can_manage_schedule(user):
            queryset = Schedule.objects.all().select_related('time_slot', 'section', 'subject', 'teacher', 'room', 'term')
        else:
            if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                queryset = Schedule.objects.filter(teacher=user.teacher_profile)
            elif user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                # Get schedules for sections the student is enrolled in
                from enrollments.models import Enrollment
                sections = Enrollment.objects.filter(student=user.student_profile, status='ENR').values_list('section_id', flat=True)
                queryset = Schedule.objects.filter(section_id__in=sections, is_active=True)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                from enrollments.models import Enrollment
                sections = Enrollment.objects.filter(student_id__in=child_ids, status='ENR').values_list('section_id', flat=True)
                queryset = Schedule.objects.filter(section_id__in=sections, is_active=True)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)

        queryset = queryset.order_by('term__academic_year', 'time_slot__day_of_week', 'time_slot__order')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ScheduleMinimalSerializer)
        return Response({
            "status": True,
            "message": "Schedules retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Timetable - Schedules"],
        request=ScheduleCreateSerializer,
        responses={201: ScheduleCreateResponseSerializer, 400: ScheduleCreateResponseSerializer, 403: ScheduleCreateResponseSerializer},
        description="Create a schedule (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = ScheduleCreateSerializer(data=request.data)
        if serializer.is_valid():
            schedule = serializer.save()
            return Response({
                "status": True,
                "message": "Schedule created.",
                "data": {
                    "id": schedule.id,
                    "time_slot": schedule.time_slot.id,
                    "section": schedule.section.id,
                    "subject": schedule.subject.id,
                    "teacher": schedule.teacher.id,
                    "room": schedule.room.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, schedule_id):
        try:
            return Schedule.objects.select_related('time_slot', 'section', 'subject', 'teacher', 'room', 'term').get(id=schedule_id)
        except Schedule.DoesNotExist:
            return None

    @extend_schema(
        tags=["Timetable - Schedules"],
        responses={200: ScheduleDetailResponseSerializer, 404: ScheduleDetailResponseSerializer, 403: ScheduleDetailResponseSerializer},
        description="Retrieve a single schedule by ID."
    )
    def get(self, request, schedule_id):
        schedule = self.get_object(schedule_id)
        if not schedule:
            return Response({
                "status": False,
                "message": "Schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_schedule(request.user, schedule):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ScheduleDisplaySerializer(schedule, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Schedule retrieved.",
            "data": {"schedule": data}
        })

    @extend_schema(
        tags=["Timetable - Schedules"],
        request=ScheduleUpdateSerializer,
        responses={200: ScheduleUpdateResponseSerializer, 400: ScheduleUpdateResponseSerializer, 403: ScheduleUpdateResponseSerializer},
        description="Update a schedule (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, schedule_id):
        return self._update(request, schedule_id, partial=False)

    @extend_schema(
        tags=["Timetable - Schedules"],
        request=ScheduleUpdateSerializer,
        responses={200: ScheduleUpdateResponseSerializer, 400: ScheduleUpdateResponseSerializer, 403: ScheduleUpdateResponseSerializer},
        description="Partially update a schedule."
    )
    @transaction.atomic
    def patch(self, request, schedule_id):
        return self._update(request, schedule_id, partial=True)

    def _update(self, request, schedule_id, partial):
        if not can_manage_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        schedule = self.get_object(schedule_id)
        if not schedule:
            return Response({
                "status": False,
                "message": "Schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ScheduleUpdateSerializer(schedule, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ScheduleDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Schedule updated.",
                "data": {"schedule": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Timetable - Schedules"],
        responses={200: ScheduleDeleteResponseSerializer, 403: ScheduleDeleteResponseSerializer, 404: ScheduleDeleteResponseSerializer},
        description="Delete a schedule (admin only)."
    )
    @transaction.atomic
    def delete(self, request, schedule_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        schedule = self.get_object(schedule_id)
        if not schedule:
            return Response({
                "status": False,
                "message": "Schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ScheduleService.delete_schedule(schedule)
        if success:
            return Response({
                "status": True,
                "message": "Schedule deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete schedule.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)