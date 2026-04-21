import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from enrollments.models import EnrollmentHold
from enrollments.models.enrollment import Enrollment
from enrollments.serializers.enrollment_hold import (
    EnrollmentHoldMinimalSerializer,
    EnrollmentHoldCreateSerializer,
    EnrollmentHoldUpdateSerializer,
    EnrollmentHoldDisplaySerializer,
)
from enrollments.services.enrollment_hold import EnrollmentHoldService
from enrollments.services.enrollment import EnrollmentService

logger = logging.getLogger(__name__)

def can_view_hold(user, hold):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return hold.enrollment.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return hold.enrollment.student in [sp.student for sp in user.parent_profile.students.all()]
    return False

def can_manage_hold(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class EnrollmentHoldCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    enrollment = serializers.IntegerField()
    reason = serializers.CharField()
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2)

class EnrollmentHoldCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHoldCreateResponseData(allow_null=True)

class EnrollmentHoldUpdateResponseData(serializers.Serializer):
    hold = EnrollmentHoldDisplaySerializer()

class EnrollmentHoldUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHoldUpdateResponseData(allow_null=True)

class EnrollmentHoldDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EnrollmentHoldDetailResponseData(serializers.Serializer):
    hold = EnrollmentHoldDisplaySerializer()

class EnrollmentHoldDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHoldDetailResponseData(allow_null=True)

class EnrollmentHoldListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EnrollmentHoldMinimalSerializer(many=True)

class EnrollmentHoldListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHoldListResponseData()

class EnrollmentHoldResolveResponseData(serializers.Serializer):
    hold = EnrollmentHoldDisplaySerializer()

class EnrollmentHoldResolveResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentHoldResolveResponseData()

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

class EnrollmentHoldListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Enrollments - Holds"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="enrollment_id", type=int, description="Filter by enrollment ID", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only unresolved holds", required=False),
        ],
        responses={200: EnrollmentHoldListResponseSerializer},
        description="List enrollment holds (admin/accounting see all, others see their own)."
    )
    def get(self, request):
        user = request.user
        enrollment_id = request.query_params.get("enrollment_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        if enrollment_id:
            enrollment = EnrollmentService.get_enrollment_by_id(enrollment_id)
            if not enrollment:
                return Response({
                    "status": False,
                    "message": "Enrollment not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
            if not can_view_hold(user, enrollment):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            holds = [EnrollmentHoldService.get_hold_by_enrollment(enrollment_id)] if EnrollmentHoldService.get_hold_by_enrollment(enrollment_id) else []
        else:
            if user.is_staff or user.role in ['ADMIN', 'REGISTRAR', 'ACCOUNTING']:
                queryset = EnrollmentHold.objects.all().select_related('enrollment')
                if active_only:
                    queryset = queryset.filter(is_resolved=False)
                holds = queryset
            else:
                # For students/parents, get holds on their enrollments
                if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                    enrollments = Enrollment.objects.filter(student=user.student_profile)
                    holds = EnrollmentHold.objects.filter(enrollment__in=enrollments)
                    if active_only:
                        holds = holds.filter(is_resolved=False)
                elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                    child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                    enrollments = Enrollment.objects.filter(student_id__in=child_ids)
                    holds = EnrollmentHold.objects.filter(enrollment__in=enrollments)
                    if active_only:
                        holds = holds.filter(is_resolved=False)
                else:
                    return Response({
                        "status": False,
                        "message": "Permission denied.",
                        "data": None
                    }, status=status.HTTP_403_FORBIDDEN)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(holds, request)
        data = wrap_paginated_data(paginator, page, request, EnrollmentHoldMinimalSerializer)
        return Response({
            "status": True,
            "message": "Enrollment holds retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Enrollments - Holds"],
        request=EnrollmentHoldCreateSerializer,
        responses={201: EnrollmentHoldCreateResponseSerializer, 400: EnrollmentHoldCreateResponseSerializer, 403: EnrollmentHoldCreateResponseSerializer},
        description="Create an enrollment hold (admin/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_hold(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = EnrollmentHoldCreateSerializer(data=request.data)
        if serializer.is_valid():
            hold = serializer.save()
            return Response({
                "status": True,
                "message": "Enrollment hold created.",
                "data": {
                    "id": hold.id,
                    "enrollment": hold.enrollment.id,
                    "reason": hold.reason,
                    "amount_due": hold.amount_due,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EnrollmentHoldDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, hold_id):
        try:
            return EnrollmentHold.objects.select_related('enrollment', 'resolved_by').get(id=hold_id)
        except EnrollmentHold.DoesNotExist:
            return None

    @extend_schema(
        tags=["Enrollments - Holds"],
        responses={200: EnrollmentHoldDetailResponseSerializer, 404: EnrollmentHoldDetailResponseSerializer, 403: EnrollmentHoldDetailResponseSerializer},
        description="Retrieve a single enrollment hold by ID."
    )
    def get(self, request, hold_id):
        hold = self.get_object(hold_id)
        if not hold:
            return Response({
                "status": False,
                "message": "Enrollment hold not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_hold(request.user, hold):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = EnrollmentHoldDisplaySerializer(hold, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Enrollment hold retrieved.",
            "data": {"hold": data}
        })

    @extend_schema(
        tags=["Enrollments - Holds"],
        request=EnrollmentHoldUpdateSerializer,
        responses={200: EnrollmentHoldUpdateResponseSerializer, 400: EnrollmentHoldUpdateResponseSerializer, 403: EnrollmentHoldUpdateResponseSerializer},
        description="Update an enrollment hold (admin/accounting only)."
    )
    @transaction.atomic
    def put(self, request, hold_id):
        return self._update(request, hold_id, partial=False)

    @extend_schema(
        tags=["Enrollments - Holds"],
        request=EnrollmentHoldUpdateSerializer,
        responses={200: EnrollmentHoldUpdateResponseSerializer, 400: EnrollmentHoldUpdateResponseSerializer, 403: EnrollmentHoldUpdateResponseSerializer},
        description="Partially update an enrollment hold."
    )
    @transaction.atomic
    def patch(self, request, hold_id):
        return self._update(request, hold_id, partial=True)

    def _update(self, request, hold_id, partial):
        if not can_manage_hold(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        hold = self.get_object(hold_id)
        if not hold:
            return Response({
                "status": False,
                "message": "Enrollment hold not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = EnrollmentHoldUpdateSerializer(hold, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EnrollmentHoldDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Enrollment hold updated.",
                "data": {"hold": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Enrollments - Holds"],
        responses={200: EnrollmentHoldDeleteResponseSerializer, 403: EnrollmentHoldDeleteResponseSerializer, 404: EnrollmentHoldDeleteResponseSerializer},
        description="Delete an enrollment hold (admin only)."
    )
    @transaction.atomic
    def delete(self, request, hold_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        hold = self.get_object(hold_id)
        if not hold:
            return Response({
                "status": False,
                "message": "Enrollment hold not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = EnrollmentHoldService.delete_hold(hold)
        if success:
            return Response({
                "status": True,
                "message": "Enrollment hold deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete enrollment hold.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EnrollmentHoldResolveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Enrollments - Holds"],
        responses={200: EnrollmentHoldResolveResponseSerializer, 403: EnrollmentHoldResolveResponseSerializer, 404: EnrollmentHoldResolveResponseSerializer},
        description="Resolve an enrollment hold (admin/accounting only)."
    )
    @transaction.atomic
    def post(self, request, hold_id):
        if not can_manage_hold(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        hold = EnrollmentHoldService.get_hold_by_id(hold_id)
        if not hold:
            return Response({
                "status": False,
                "message": "Enrollment hold not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if hold.is_resolved:
            return Response({
                "status": False,
                "message": "Hold already resolved.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = EnrollmentHoldService.resolve_hold(hold, request.user)
        data = EnrollmentHoldDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Enrollment hold resolved.",
            "data": {"hold": data}
        })