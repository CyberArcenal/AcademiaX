import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from fees.models import CollectionReport
from fees.serializers.collection import (
    CollectionReportMinimalSerializer,
    CollectionReportCreateSerializer,
    CollectionReportUpdateSerializer,
    CollectionReportDisplaySerializer,
)
from fees.services.collection import CollectionReportService

logger = logging.getLogger(__name__)

def can_manage_collection(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class CollectionReportCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    report_date = serializers.DateField()
    total_collections = serializers.DecimalField(max_digits=15, decimal_places=2)

class CollectionReportCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CollectionReportCreateResponseData(allow_null=True)

class CollectionReportUpdateResponseData(serializers.Serializer):
    report = CollectionReportDisplaySerializer()

class CollectionReportUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CollectionReportUpdateResponseData(allow_null=True)

class CollectionReportDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class CollectionReportDetailResponseData(serializers.Serializer):
    report = CollectionReportDisplaySerializer()

class CollectionReportDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CollectionReportDetailResponseData(allow_null=True)

class CollectionReportListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = CollectionReportMinimalSerializer(many=True)

class CollectionReportListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CollectionReportListResponseData()

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

class CollectionReportListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Fees - Collection Reports"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="start_date", type=str, description="Start date (YYYY-MM-DD)", required=False),
            OpenApiParameter(name="end_date", type=str, description="End date (YYYY-MM-DD)", required=False),
        ],
        responses={200: CollectionReportListResponseSerializer},
        description="List collection reports (admin/accounting only)."
    )
    def get(self, request):
        if not can_manage_collection(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        from datetime import datetime
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        reports = CollectionReportService.get_reports(date_range_start=start, date_range_end=end)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(reports, request)
        data = wrap_paginated_data(paginator, page, request, CollectionReportMinimalSerializer)
        return Response({
            "status": True,
            "message": "Collection reports retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Fees - Collection Reports"],
        request=CollectionReportCreateSerializer,
        responses={201: CollectionReportCreateResponseSerializer, 400: CollectionReportCreateResponseSerializer, 403: CollectionReportCreateResponseSerializer},
        description="Generate a collection report for a specific date (admin/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_collection(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Set generated_by to current user
        data = request.data.copy()
        data['generated_by_id'] = request.user.id
        serializer = CollectionReportCreateSerializer(data=data)
        if serializer.is_valid():
            report = serializer.save()
            return Response({
                "status": True,
                "message": "Collection report generated.",
                "data": {
                    "id": report.id,
                    "report_date": report.report_date,
                    "total_collections": report.total_collections,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CollectionReportDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, report_id):
        try:
            return CollectionReport.objects.select_related('generated_by').get(id=report_id)
        except CollectionReport.DoesNotExist:
            return None

    @extend_schema(
        tags=["Fees - Collection Reports"],
        responses={200: CollectionReportDetailResponseSerializer, 404: CollectionReportDetailResponseSerializer, 403: CollectionReportDetailResponseSerializer},
        description="Retrieve a single collection report by ID."
    )
    def get(self, request, report_id):
        if not can_manage_collection(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report = self.get_object(report_id)
        if not report:
            return Response({
                "status": False,
                "message": "Collection report not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = CollectionReportDisplaySerializer(report, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Collection report retrieved.",
            "data": {"report": data}
        })

    @extend_schema(
        tags=["Fees - Collection Reports"],
        request=CollectionReportUpdateSerializer,
        responses={200: CollectionReportUpdateResponseSerializer, 400: CollectionReportUpdateResponseSerializer, 403: CollectionReportUpdateResponseSerializer},
        description="Update a collection report (e.g., add notes)."
    )
    @transaction.atomic
    def put(self, request, report_id):
        return self._update(request, report_id, partial=False)

    @extend_schema(
        tags=["Fees - Collection Reports"],
        request=CollectionReportUpdateSerializer,
        responses={200: CollectionReportUpdateResponseSerializer, 400: CollectionReportUpdateResponseSerializer, 403: CollectionReportUpdateResponseSerializer},
        description="Partially update a collection report."
    )
    @transaction.atomic
    def patch(self, request, report_id):
        return self._update(request, report_id, partial=True)

    def _update(self, request, report_id, partial):
        if not can_manage_collection(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report = self.get_object(report_id)
        if not report:
            return Response({
                "status": False,
                "message": "Collection report not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = CollectionReportUpdateSerializer(report, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = CollectionReportDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Collection report updated.",
                "data": {"report": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Fees - Collection Reports"],
        responses={200: CollectionReportDeleteResponseSerializer, 403: CollectionReportDeleteResponseSerializer, 404: CollectionReportDeleteResponseSerializer},
        description="Delete a collection report (admin only)."
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
                "message": "Collection report not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = CollectionReportService.delete_report(report)
        if success:
            return Response({
                "status": True,
                "message": "Collection report deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete collection report.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)