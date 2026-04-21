import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from enrollments.models import EnrollmentHistory
from enrollments.serializers.enrollment_history import (
    EnrollmentHistoryMinimalSerializer,
    EnrollmentHistoryCreateSerializer,
    EnrollmentHistoryUpdateSerializer,
    EnrollmentHistoryDisplaySerializer,
)
from enrollments.services.enrollment_history import EnrollmentHistoryService
from enrollments.services.enrollment import EnrollmentService

logger = logging.getLogger(__name__)

def can_view_enrollment_history(user, history):
    # Same permission as viewing enrollment
    if user.is_staff:
        return True
    if user.role == 'TEACHER':
        return history.enrollment.section.teacher_assignments.filter(teacher__user=user, is_active=True).exists()
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return history.enrollment.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return history.enrollment.student in [sp.student for sp in user.parent_profile.students.all()]
    return False

def can_manage_enrollment_history(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class EnrollmentHistoryCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    enrollment = serializers.IntegerField()
    previous_status = serializers.CharField(allow_null=True)
    new_status = serializers.CharField()

class EnrollmentHistoryCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHistoryCreateResponseData(allow_null=True)

class EnrollmentHistoryUpdateResponseData(serializers.Serializer):
    history = EnrollmentHistoryDisplaySerializer()

class EnrollmentHistoryUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHistoryUpdateResponseData(allow_null=True)

class EnrollmentHistoryDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EnrollmentHistoryDetailResponseData(serializers.Serializer):
    history = EnrollmentHistoryDisplaySerializer()

class EnrollmentHistoryDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHistoryDetailResponseData(allow_null=True)

class EnrollmentHistoryListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EnrollmentHistoryMinimalSerializer(many=True)

class EnrollmentHistoryListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHistoryListResponseData()

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

class EnrollmentHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Enrollments - History"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="enrollment_id", type=int, description="Filter by enrollment ID", required=True),
        ],
        responses={200: EnrollmentHistoryListResponseSerializer},
        description="List enrollment history entries for a specific enrollment (requires view permission on enrollment)."
    )
    def get(self, request):
        enrollment_id = request.query_params.get("enrollment_id")
        if not enrollment_id:
            return Response({
                "status": False,
                "message": "enrollment_id parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        enrollment = EnrollmentService.get_enrollment_by_id(enrollment_id)
        if not enrollment:
            return Response({
                "status": False,
                "message": "Enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_enrollment_history(request.user, enrollment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        history = EnrollmentHistoryService.get_history_by_enrollment(enrollment_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(history, request)
        data = wrap_paginated_data(paginator, page, request, EnrollmentHistoryMinimalSerializer)
        return Response({
            "status": True,
            "message": "Enrollment history retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Enrollments - History"],
        request=EnrollmentHistoryCreateSerializer,
        responses={201: EnrollmentHistoryCreateResponseSerializer, 400: EnrollmentHistoryCreateResponseSerializer, 403: EnrollmentHistoryCreateResponseSerializer},
        description="Create an enrollment history entry (usually internal, but available for admin)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_enrollment_history(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = EnrollmentHistoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            history = serializer.save()
            return Response({
                "status": True,
                "message": "Enrollment history entry created.",
                "data": {
                    "id": history.id,
                    "enrollment": history.enrollment.id,
                    "previous_status": history.previous_status,
                    "new_status": history.new_status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EnrollmentHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, history_id):
        try:
            return EnrollmentHistory.objects.select_related('enrollment', 'changed_by').get(id=history_id)
        except EnrollmentHistory.DoesNotExist:
            return None

    @extend_schema(
        tags=["Enrollments - History"],
        responses={200: EnrollmentHistoryDetailResponseSerializer, 404: EnrollmentHistoryDetailResponseSerializer, 403: EnrollmentHistoryDetailResponseSerializer},
        description="Retrieve a single enrollment history entry by ID."
    )
    def get(self, request, history_id):
        history = self.get_object(history_id)
        if not history:
            return Response({
                "status": False,
                "message": "History entry not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_enrollment_history(request.user, history):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = EnrollmentHistoryDisplaySerializer(history, context={"request": request}).data
        return Response({
            "status": True,
            "message": "History entry retrieved.",
            "data": {"history": data}
        })

    @extend_schema(
        tags=["Enrollments - History"],
        request=EnrollmentHistoryUpdateSerializer,
        responses={200: EnrollmentHistoryUpdateResponseSerializer, 400: EnrollmentHistoryUpdateResponseSerializer, 403: EnrollmentHistoryUpdateResponseSerializer},
        description="Update an enrollment history entry (admin only, usually not allowed)."
    )
    @transaction.atomic
    def put(self, request, history_id):
        return self._update(request, history_id, partial=False)

    @extend_schema(
        tags=["Enrollments - History"],
        request=EnrollmentHistoryUpdateSerializer,
        responses={200: EnrollmentHistoryUpdateResponseSerializer, 400: EnrollmentHistoryUpdateResponseSerializer, 403: EnrollmentHistoryUpdateResponseSerializer},
        description="Partially update an enrollment history entry."
    )
    @transaction.atomic
    def patch(self, request, history_id):
        return self._update(request, history_id, partial=True)

    def _update(self, request, history_id, partial):
        if not can_manage_enrollment_history(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        history = self.get_object(history_id)
        if not history:
            return Response({
                "status": False,
                "message": "History entry not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Typically history entries are immutable; but allow remarks update if needed.
        serializer = EnrollmentHistoryUpdateSerializer(history, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EnrollmentHistoryDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "History entry updated.",
                "data": {"history": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Enrollments - History"],
        responses={200: EnrollmentHistoryDeleteResponseSerializer, 403: EnrollmentHistoryDeleteResponseSerializer, 404: EnrollmentHistoryDeleteResponseSerializer},
        description="Delete an enrollment history entry (admin only)."
    )
    @transaction.atomic
    def delete(self, request, history_id):
        if not can_manage_enrollment_history(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        history = self.get_object(history_id)
        if not history:
            return Response({
                "status": False,
                "message": "History entry not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = EnrollmentHistoryService.delete_history(history)
        if success:
            return Response({
                "status": True,
                "message": "History entry deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete history entry.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)