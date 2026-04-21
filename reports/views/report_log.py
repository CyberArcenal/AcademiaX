import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from reports.models import ReportLog
from reports.serializers.report_log import (
    ReportLogMinimalSerializer,
    ReportLogCreateSerializer,
    ReportLogUpdateSerializer,
    ReportLogDisplaySerializer,
)
from reports.services.report_log import ReportLogService

logger = logging.getLogger(__name__)

def can_view_report_log(user, log):
    if user.is_staff:
        return True
    # Users can see logs of reports they generated
    return log.report.generated_by == user

def can_manage_log(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REPORT_VIEWER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ReportLogCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    report = serializers.IntegerField()
    action = serializers.CharField()

class ReportLogCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportLogCreateResponseData(allow_null=True)

class ReportLogUpdateResponseData(serializers.Serializer):
    log = ReportLogDisplaySerializer()

class ReportLogUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportLogUpdateResponseData(allow_null=True)

class ReportLogDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ReportLogDetailResponseData(serializers.Serializer):
    log = ReportLogDisplaySerializer()

class ReportLogDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportLogDetailResponseData(allow_null=True)

class ReportLogListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ReportLogMinimalSerializer(many=True)

class ReportLogListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportLogListResponseData()

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

class ReportLogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Reports - Logs"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="report_id", type=int, description="Filter by report ID", required=False),
            OpenApiParameter(name="action", type=str, description="Filter by action", required=False),
        ],
        responses={200: ReportLogListResponseSerializer},
        description="List report logs (admin/report viewer sees all, others see logs of their reports)."
    )
    def get(self, request):
        user = request.user
        report_id = request.query_params.get("report_id")
        action_filter = request.query_params.get("action")

        if user.is_staff or can_manage_log(user):
            queryset = ReportLog.objects.all().select_related('report', 'performed_by')
        else:
            # Users see logs of reports they generated
            queryset = ReportLog.objects.filter(report__generated_by=user)

        if report_id:
            queryset = queryset.filter(report_id=report_id)
        if action_filter:
            queryset = queryset.filter(action=action_filter)

        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ReportLogMinimalSerializer)
        return Response({
            "status": True,
            "message": "Report logs retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Reports - Logs"],
        request=ReportLogCreateSerializer,
        responses={201: ReportLogCreateResponseSerializer, 400: ReportLogCreateResponseSerializer, 403: ReportLogCreateResponseSerializer},
        description="Create a report log (usually internal, but available for admin)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_log(request.user):
            return Response({
                "status": False,
                "message": "Admin or report viewer permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = request.data.copy()
        data['performed_by_id'] = request.user.id
        serializer = ReportLogCreateSerializer(data=data)
        if serializer.is_valid():
            log = serializer.save()
            return Response({
                "status": True,
                "message": "Report log created.",
                "data": {
                    "id": log.id,
                    "report": log.report.id,
                    "action": log.action,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReportLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, log_id):
        try:
            return ReportLog.objects.select_related('report', 'performed_by').get(id=log_id)
        except ReportLog.DoesNotExist:
            return None

    @extend_schema(
        tags=["Reports - Logs"],
        responses={200: ReportLogDetailResponseSerializer, 404: ReportLogDetailResponseSerializer, 403: ReportLogDetailResponseSerializer},
        description="Retrieve a single report log by ID."
    )
    def get(self, request, log_id):
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Report log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_report_log(request.user, log):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ReportLogDisplaySerializer(log, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Report log retrieved.",
            "data": {"log": data}
        })

    @extend_schema(
        tags=["Reports - Logs"],
        request=ReportLogUpdateSerializer,
        responses={200: ReportLogUpdateResponseSerializer, 400: ReportLogUpdateResponseSerializer, 403: ReportLogUpdateResponseSerializer},
        description="Update a report log (usually not allowed, but provided for completeness)."
    )
    @transaction.atomic
    def put(self, request, log_id):
        return self._update(request, log_id, partial=False)

    @extend_schema(
        tags=["Reports - Logs"],
        request=ReportLogUpdateSerializer,
        responses={200: ReportLogUpdateResponseSerializer, 400: ReportLogUpdateResponseSerializer, 403: ReportLogUpdateResponseSerializer},
        description="Partially update a report log."
    )
    @transaction.atomic
    def patch(self, request, log_id):
        return self._update(request, log_id, partial=True)

    def _update(self, request, log_id, partial):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Report log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Typically logs are immutable, but allow updating details if needed
        serializer = ReportLogUpdateSerializer(log, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ReportLogDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Report log updated.",
                "data": {"log": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Reports - Logs"],
        responses={200: ReportLogDeleteResponseSerializer, 403: ReportLogDeleteResponseSerializer, 404: ReportLogDeleteResponseSerializer},
        description="Delete a report log (admin only)."
    )
    @transaction.atomic
    def delete(self, request, log_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Report log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ReportLogService.delete_log(log)
        if success:
            return Response({
                "status": True,
                "message": "Report log deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete report log.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)