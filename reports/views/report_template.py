import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from reports.models import ReportTemplate
from reports.serializers.report_template import (
    ReportTemplateMinimalSerializer,
    ReportTemplateCreateSerializer,
    ReportTemplateUpdateSerializer,
    ReportTemplateDisplaySerializer,
)
from reports.services.report_template import ReportTemplateService

logger = logging.getLogger(__name__)

def can_manage_template(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REPORT_VIEWER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TemplateCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    report_type = serializers.CharField()

class TemplateCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TemplateCreateResponseData(allow_null=True)

class TemplateUpdateResponseData(serializers.Serializer):
    template = ReportTemplateDisplaySerializer()

class TemplateUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TemplateUpdateResponseData(allow_null=True)

class TemplateDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TemplateDetailResponseData(serializers.Serializer):
    template = ReportTemplateDisplaySerializer()

class TemplateDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TemplateDetailResponseData(allow_null=True)

class TemplateListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ReportTemplateMinimalSerializer(many=True)

class TemplateListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TemplateListResponseData()

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

class ReportTemplateListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Reports - Templates"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="report_type", type=str, description="Filter by report type", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active templates", required=False),
        ],
        responses={200: TemplateListResponseSerializer},
        description="List report templates (admin/report viewer only)."
    )
    def get(self, request):
        if not can_manage_template(request.user):
            return Response({
                "status": False,
                "message": "Admin or report viewer permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report_type = request.query_params.get("report_type")
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if report_type:
            templates = ReportTemplateService.get_templates_by_type(report_type, active_only=active_only)
        else:
            queryset = ReportTemplate.objects.all()
            if active_only:
                queryset = queryset.filter(is_active=True)
            templates = queryset
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(templates, request)
        data = wrap_paginated_data(paginator, page, request, ReportTemplateMinimalSerializer)
        return Response({
            "status": True,
            "message": "Report templates retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Reports - Templates"],
        request=ReportTemplateCreateSerializer,
        responses={201: TemplateCreateResponseSerializer, 400: TemplateCreateResponseSerializer, 403: TemplateCreateResponseSerializer},
        description="Create a report template (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Set created_by to current user
        data = request.data.copy()
        data['created_by_id'] = request.user.id
        serializer = ReportTemplateCreateSerializer(data=data)
        if serializer.is_valid():
            template = serializer.save()
            return Response({
                "status": True,
                "message": "Report template created.",
                "data": {
                    "id": template.id,
                    "name": template.name,
                    "report_type": template.report_type,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReportTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, template_id):
        try:
            return ReportTemplate.objects.select_related('created_by').get(id=template_id)
        except ReportTemplate.DoesNotExist:
            return None

    @extend_schema(
        tags=["Reports - Templates"],
        responses={200: TemplateDetailResponseSerializer, 404: TemplateDetailResponseSerializer, 403: TemplateDetailResponseSerializer},
        description="Retrieve a single report template by ID."
    )
    def get(self, request, template_id):
        if not can_manage_template(request.user):
            return Response({
                "status": False,
                "message": "Admin or report viewer permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        template = self.get_object(template_id)
        if not template:
            return Response({
                "status": False,
                "message": "Report template not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = ReportTemplateDisplaySerializer(template, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Report template retrieved.",
            "data": {"template": data}
        })

    @extend_schema(
        tags=["Reports - Templates"],
        request=ReportTemplateUpdateSerializer,
        responses={200: TemplateUpdateResponseSerializer, 400: TemplateUpdateResponseSerializer, 403: TemplateUpdateResponseSerializer},
        description="Update a report template (admin only)."
    )
    @transaction.atomic
    def put(self, request, template_id):
        return self._update(request, template_id, partial=False)

    @extend_schema(
        tags=["Reports - Templates"],
        request=ReportTemplateUpdateSerializer,
        responses={200: TemplateUpdateResponseSerializer, 400: TemplateUpdateResponseSerializer, 403: TemplateUpdateResponseSerializer},
        description="Partially update a report template."
    )
    @transaction.atomic
    def patch(self, request, template_id):
        return self._update(request, template_id, partial=True)

    def _update(self, request, template_id, partial):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        template = self.get_object(template_id)
        if not template:
            return Response({
                "status": False,
                "message": "Report template not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ReportTemplateUpdateSerializer(template, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ReportTemplateDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Report template updated.",
                "data": {"template": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Reports - Templates"],
        responses={200: TemplateDeleteResponseSerializer, 403: TemplateDeleteResponseSerializer, 404: TemplateDeleteResponseSerializer},
        description="Delete a report template (admin only)."
    )
    @transaction.atomic
    def delete(self, request, template_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        template = self.get_object(template_id)
        if not template:
            return Response({
                "status": False,
                "message": "Report template not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ReportTemplateService.delete_template(template)
        if success:
            return Response({
                "status": True,
                "message": "Report template deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete report template.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportTemplateSetDefaultView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Reports - Templates"],
        responses={200: TemplateDetailResponseSerializer, 403: TemplateDetailResponseSerializer, 404: TemplateDetailResponseSerializer},
        description="Set a report template as default for its report type (admin only)."
    )
    @transaction.atomic
    def post(self, request, template_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        template = ReportTemplateService.get_template_by_id(template_id)
        if not template:
            return Response({
                "status": False,
                "message": "Report template not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = ReportTemplateService.set_as_default(template)
        data = ReportTemplateDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Default template updated.",
            "data": {"template": data}
        })