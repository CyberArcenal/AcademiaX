import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from reports.models import Report
from reports.serializers.report import (
    ReportMinimalSerializer,
    ReportCreateSerializer,
    ReportUpdateSerializer,
    ReportDisplaySerializer,
)
from reports.services.report import ReportService

logger = logging.getLogger(__name__)

def can_view_report(user, report):
    if user.is_staff:
        return True
    # Users can see reports they generated
    return report.generated_by == user

def can_manage_report(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REPORT_VIEWER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ReportCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()

class ReportCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportCreateResponseData(allow_null=True)

class ReportUpdateResponseData(serializers.Serializer):
    report = ReportDisplaySerializer()

class ReportUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportUpdateResponseData(allow_null=True)

class ReportDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ReportDetailResponseData(serializers.Serializer):
    report = ReportDisplaySerializer()

class ReportDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportDetailResponseData(allow_null=True)

class ReportListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ReportMinimalSerializer(many=True)

class ReportListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportListResponseData()

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

class ReportListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Reports"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="report_type", type=str, description="Filter by report type", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by status", required=False),
        ],
        responses={200: ReportListResponseSerializer},
        description="List reports (admin sees all, users see their own)."
    )
    def get(self, request):
        user = request.user
        report_type = request.query_params.get("report_type")
        status_filter = request.query_params.get("status")

        if user.is_staff or can_manage_report(user):
            queryset = Report.objects.all().select_related('generated_by')
        else:
            queryset = Report.objects.filter(generated_by=user)

        if report_type:
            queryset = queryset.filter(report_type=report_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ReportMinimalSerializer)
        return Response({
            "status": True,
            "message": "Reports retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Reports"],
        request=ReportCreateSerializer,
        responses={201: ReportCreateResponseSerializer, 400: ReportCreateResponseSerializer, 403: ReportCreateResponseSerializer},
        description="Create a report generation request."
    )
    @transaction.atomic
    def post(self, request):
        data = request.data.copy()
        data['generated_by_id'] = request.user.id
        serializer = ReportCreateSerializer(data=data)
        if serializer.is_valid():
            report = serializer.save()
            # Optionally trigger async report generation here
            return Response({
                "status": True,
                "message": "Report generation started.",
                "data": {
                    "id": report.id,
                    "name": report.name,
                    "status": report.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReportDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, report_id):
        try:
            return Report.objects.select_related('generated_by').get(id=report_id)
        except Report.DoesNotExist:
            return None

    @extend_schema(
        tags=["Reports"],
        responses={200: ReportDetailResponseSerializer, 404: ReportDetailResponseSerializer, 403: ReportDetailResponseSerializer},
        description="Retrieve a single report by ID."
    )
    def get(self, request, report_id):
        report = self.get_object(report_id)
        if not report:
            return Response({
                "status": False,
                "message": "Report not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_report(request.user, report):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ReportDisplaySerializer(report, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Report retrieved.",
            "data": {"report": data}
        })

    @extend_schema(
        tags=["Reports"],
        request=ReportUpdateSerializer,
        responses={200: ReportUpdateResponseSerializer, 400: ReportUpdateResponseSerializer, 403: ReportUpdateResponseSerializer},
        description="Update a report (e.g., mark completed, set file URL)."
    )
    @transaction.atomic
    def put(self, request, report_id):
        return self._update(request, report_id, partial=False)

    @extend_schema(
        tags=["Reports"],
        request=ReportUpdateSerializer,
        responses={200: ReportUpdateResponseSerializer, 400: ReportUpdateResponseSerializer, 403: ReportUpdateResponseSerializer},
        description="Partially update a report."
    )
    @transaction.atomic
    def patch(self, request, report_id):
        return self._update(request, report_id, partial=True)

    def _update(self, request, report_id, partial):
        if not can_manage_report(request.user):
            return Response({
                "status": False,
                "message": "Admin or report viewer permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report = self.get_object(report_id)
        if not report:
            return Response({
                "status": False,
                "message": "Report not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ReportUpdateSerializer(report, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ReportDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Report updated.",
                "data": {"report": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Reports"],
        responses={200: ReportDeleteResponseSerializer, 403: ReportDeleteResponseSerializer, 404: ReportDeleteResponseSerializer},
        description="Delete a report (admin only)."
    )
    @transaction.atomic
    def delete(self, request, report_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report = self.get_object(report_id)
        if not report:
            return Response({
                "status": False,
                "message": "Report not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ReportService.delete_report(report)
        if success:
            return Response({
                "status": True,
                "message": "Report deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete report.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Reports"],
        responses={200: serializers.Serializer, 403: serializers.Serializer, 404: serializers.Serializer},
        description="Download a completed report file (redirect to file URL)."
    )
    def get(self, request, report_id):
        report = ReportService.get_report_by_id(report_id)
        if not report:
            return Response({
                "status": False,
                "message": "Report not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_report(request.user, report):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if report.status != 'CMP':
            return Response({
                "status": False,
                "message": "Report not ready for download.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        # Redirect to file URL or return URL in response
        return Response({
            "status": True,
            "message": "Report download URL.",
            "data": {"download_url": report.file_url}
        })