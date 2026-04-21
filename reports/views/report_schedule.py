import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from reports.models import ReportSchedule
from reports.serializers.report_schedule import (
    ReportScheduleMinimalSerializer,
    ReportScheduleCreateSerializer,
    ReportScheduleUpdateSerializer,
    ReportScheduleDisplaySerializer,
)
from reports.services.report_schedule import ReportScheduleService

logger = logging.getLogger(__name__)

def can_manage_schedule(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REPORT_VIEWER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ScheduleCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cron_expression = serializers.CharField()
    is_active = serializers.BooleanField()

class ScheduleCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScheduleCreateResponseData(allow_null=True)

class ScheduleUpdateResponseData(serializers.Serializer):
    schedule = ReportScheduleDisplaySerializer()

class ScheduleUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScheduleUpdateResponseData(allow_null=True)

class ScheduleDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ScheduleDetailResponseData(serializers.Serializer):
    schedule = ReportScheduleDisplaySerializer()

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
    results = ReportScheduleMinimalSerializer(many=True)

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

class ReportScheduleListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Reports - Schedules"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active schedules", required=False),
        ],
        responses={200: ScheduleListResponseSerializer},
        description="List report schedules (admin/report viewer only)."
    )
    def get(self, request):
        if not can_manage_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or report viewer permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if active_only:
            schedules = ReportScheduleService.get_active_schedules()
        else:
            schedules = ReportSchedule.objects.all()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(schedules, request)
        data = wrap_paginated_data(paginator, page, request, ReportScheduleMinimalSerializer)
        return Response({
            "status": True,
            "message": "Report schedules retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Reports - Schedules"],
        request=ReportScheduleCreateSerializer,
        responses={201: ScheduleCreateResponseSerializer, 400: ScheduleCreateResponseSerializer, 403: ScheduleCreateResponseSerializer},
        description="Create a report schedule (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = request.data.copy()
        data['created_by_id'] = request.user.id
        serializer = ReportScheduleCreateSerializer(data=data)
        if serializer.is_valid():
            schedule = serializer.save()
            return Response({
                "status": True,
                "message": "Report schedule created.",
                "data": {
                    "id": schedule.id,
                    "name": schedule.name,
                    "cron_expression": schedule.cron_expression,
                    "is_active": schedule.is_active,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReportScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, schedule_id):
        try:
            return ReportSchedule.objects.select_related('created_by').get(id=schedule_id)
        except ReportSchedule.DoesNotExist:
            return None

    @extend_schema(
        tags=["Reports - Schedules"],
        responses={200: ScheduleDetailResponseSerializer, 404: ScheduleDetailResponseSerializer, 403: ScheduleDetailResponseSerializer},
        description="Retrieve a single report schedule by ID."
    )
    def get(self, request, schedule_id):
        if not can_manage_schedule(request.user):
            return Response({
                "status": False,
                "message": "Admin or report viewer permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        schedule = self.get_object(schedule_id)
        if not schedule:
            return Response({
                "status": False,
                "message": "Report schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = ReportScheduleDisplaySerializer(schedule, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Report schedule retrieved.",
            "data": {"schedule": data}
        })

    @extend_schema(
        tags=["Reports - Schedules"],
        request=ReportScheduleUpdateSerializer,
        responses={200: ScheduleUpdateResponseSerializer, 400: ScheduleUpdateResponseSerializer, 403: ScheduleUpdateResponseSerializer},
        description="Update a report schedule (admin only)."
    )
    @transaction.atomic
    def put(self, request, schedule_id):
        return self._update(request, schedule_id, partial=False)

    @extend_schema(
        tags=["Reports - Schedules"],
        request=ReportScheduleUpdateSerializer,
        responses={200: ScheduleUpdateResponseSerializer, 400: ScheduleUpdateResponseSerializer, 403: ScheduleUpdateResponseSerializer},
        description="Partially update a report schedule."
    )
    @transaction.atomic
    def patch(self, request, schedule_id):
        return self._update(request, schedule_id, partial=True)

    def _update(self, request, schedule_id, partial):
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
                "message": "Report schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ReportScheduleUpdateSerializer(schedule, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ReportScheduleDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Report schedule updated.",
                "data": {"schedule": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Reports - Schedules"],
        responses={200: ScheduleDeleteResponseSerializer, 403: ScheduleDeleteResponseSerializer, 404: ScheduleDeleteResponseSerializer},
        description="Delete a report schedule (admin only)."
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
                "message": "Report schedule not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ReportScheduleService.delete_schedule(schedule)
        if success:
            return Response({
                "status": True,
                "message": "Report schedule deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete report schedule.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)