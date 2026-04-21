import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from parents.models import ParentCommunicationLog
from parents.serializers.parent_communication import (
    ParentCommunicationLogMinimalSerializer,
    ParentCommunicationLogCreateSerializer,
    ParentCommunicationLogUpdateSerializer,
    ParentCommunicationLogDisplaySerializer,
)
from parents.services.parent_communication import ParentCommunicationLogService

logger = logging.getLogger(__name__)

def can_view_communication(user, log):
    if user.is_staff:
        return True
    # Parent can see their own communication logs
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return log.parent == user.parent_profile
    # Staff who sent the communication can view? Optional
    if log.sent_by == user:
        return True
    return False

def can_manage_communication(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR', 'TEACHER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ParentCommunicationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    parent = serializers.IntegerField()
    subject = serializers.CharField()
    channel = serializers.CharField()
    direction = serializers.CharField()

class ParentCommunicationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentCommunicationCreateResponseData(allow_null=True)

class ParentCommunicationUpdateResponseData(serializers.Serializer):
    log = ParentCommunicationLogDisplaySerializer()

class ParentCommunicationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentCommunicationUpdateResponseData(allow_null=True)

class ParentCommunicationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ParentCommunicationDetailResponseData(serializers.Serializer):
    log = ParentCommunicationLogDisplaySerializer()

class ParentCommunicationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentCommunicationDetailResponseData(allow_null=True)

class ParentCommunicationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ParentCommunicationLogMinimalSerializer(many=True)

class ParentCommunicationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentCommunicationListResponseData()

class ParentCommunicationResolveResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentCommunicationDetailResponseData()

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

class ParentCommunicationLogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Parents - Communication"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="parent_id", type=int, description="Filter by parent ID", required=False),
            OpenApiParameter(name="unresolved_only", type=bool, description="Only unresolved logs", required=False),
        ],
        responses={200: ParentCommunicationListResponseSerializer},
        description="List parent communication logs (filtered by role)."
    )
    def get(self, request):
        user = request.user
        parent_id = request.query_params.get("parent_id")
        unresolved_only = request.query_params.get("unresolved_only", "false").lower() == "true"

        if user.is_staff or can_manage_communication(user):
            queryset = ParentCommunicationLog.objects.all().select_related('parent', 'sent_by', 'resolved_by')
        else:
            if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                queryset = ParentCommunicationLog.objects.filter(parent=user.parent_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        if unresolved_only:
            queryset = queryset.filter(is_resolved=False)

        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ParentCommunicationLogMinimalSerializer)
        return Response({
            "status": True,
            "message": "Communication logs retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Parents - Communication"],
        request=ParentCommunicationLogCreateSerializer,
        responses={201: ParentCommunicationCreateResponseSerializer, 400: ParentCommunicationCreateResponseSerializer, 403: ParentCommunicationCreateResponseSerializer},
        description="Create a parent communication log (staff only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_communication(request.user):
            return Response({
                "status": False,
                "message": "Staff permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Set sent_by to current user
        data = request.data.copy()
        data['sent_by_id'] = request.user.id
        serializer = ParentCommunicationLogCreateSerializer(data=data)
        if serializer.is_valid():
            log = serializer.save()
            return Response({
                "status": True,
                "message": "Communication log created.",
                "data": {
                    "id": log.id,
                    "parent": log.parent.id,
                    "subject": log.subject,
                    "channel": log.channel,
                    "direction": log.direction,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ParentCommunicationLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, log_id):
        try:
            return ParentCommunicationLog.objects.select_related('parent', 'sent_by', 'resolved_by').get(id=log_id)
        except ParentCommunicationLog.DoesNotExist:
            return None

    @extend_schema(
        tags=["Parents - Communication"],
        responses={200: ParentCommunicationDetailResponseSerializer, 404: ParentCommunicationDetailResponseSerializer, 403: ParentCommunicationDetailResponseSerializer},
        description="Retrieve a single communication log by ID."
    )
    def get(self, request, log_id):
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Communication log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_communication(request.user, log):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ParentCommunicationLogDisplaySerializer(log, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Communication log retrieved.",
            "data": {"log": data}
        })

    @extend_schema(
        tags=["Parents - Communication"],
        request=ParentCommunicationLogUpdateSerializer,
        responses={200: ParentCommunicationUpdateResponseSerializer, 400: ParentCommunicationUpdateResponseSerializer, 403: ParentCommunicationUpdateResponseSerializer},
        description="Update a communication log (e.g., add notes)."
    )
    @transaction.atomic
    def put(self, request, log_id):
        return self._update(request, log_id, partial=False)

    @extend_schema(
        tags=["Parents - Communication"],
        request=ParentCommunicationLogUpdateSerializer,
        responses={200: ParentCommunicationUpdateResponseSerializer, 400: ParentCommunicationUpdateResponseSerializer, 403: ParentCommunicationUpdateResponseSerializer},
        description="Partially update a communication log."
    )
    @transaction.atomic
    def patch(self, request, log_id):
        return self._update(request, log_id, partial=True)

    def _update(self, request, log_id, partial):
        if not can_manage_communication(request.user):
            return Response({
                "status": False,
                "message": "Staff permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Communication log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ParentCommunicationLogUpdateSerializer(log, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ParentCommunicationLogDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Communication log updated.",
                "data": {"log": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Parents - Communication"],
        responses={200: ParentCommunicationDeleteResponseSerializer, 403: ParentCommunicationDeleteResponseSerializer, 404: ParentCommunicationDeleteResponseSerializer},
        description="Delete a communication log (admin only)."
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
                "message": "Communication log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ParentCommunicationLogService.delete_log(log)
        if success:
            return Response({
                "status": True,
                "message": "Communication log deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete communication log.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentCommunicationLogResolveView(APIView):
    permission_classes = [IsAuthenticated]

    class ResolveSerializer(serializers.Serializer):
        resolution_notes = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["Parents - Communication"],
        request=ResolveSerializer,
        responses={200: ParentCommunicationResolveResponseSerializer, 400: ParentCommunicationResolveResponseSerializer, 403: ParentCommunicationResolveResponseSerializer},
        description="Mark a communication log as resolved (staff only)."
    )
    @transaction.atomic
    def post(self, request, log_id):
        if not can_manage_communication(request.user):
            return Response({
                "status": False,
                "message": "Staff permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = ParentCommunicationLogService.get_log_by_id(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Communication log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if log.is_resolved:
            return Response({
                "status": False,
                "message": "Log already resolved.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.ResolveSerializer(data=request.data)
        resolution_notes = serializer.validated_data.get('resolution_notes', '') if serializer.is_valid() else ''
        if not serializer.is_valid():
            # Allow empty resolution notes
            pass
        updated = ParentCommunicationLogService.resolve_log(log, request.user, resolution_notes)
        data = ParentCommunicationLogDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Communication log resolved.",
            "data": {"log": data}
        })