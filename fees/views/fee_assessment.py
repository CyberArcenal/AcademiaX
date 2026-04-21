import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from fees.models import FeeAssessment
from fees.serializers.fee_assessment import (
    FeeAssessmentMinimalSerializer,
    FeeAssessmentCreateSerializer,
    FeeAssessmentUpdateSerializer,
    FeeAssessmentDisplaySerializer,
)
from fees.services.fee_assessment import FeeAssessmentService
from enrollments.services.enrollment import EnrollmentService

logger = logging.getLogger(__name__)

def can_view_fee_assessment(user, assessment):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return assessment.enrollment.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return assessment.enrollment.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role in ['ADMIN', 'ACCOUNTING', 'REGISTRAR']:
        return True
    return False

def can_manage_fee_assessment(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class FeeAssessmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    enrollment = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    due_date = serializers.DateField()

class FeeAssessmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeAssessmentCreateResponseData(allow_null=True)

class FeeAssessmentUpdateResponseData(serializers.Serializer):
    assessment = FeeAssessmentDisplaySerializer()

class FeeAssessmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeAssessmentUpdateResponseData(allow_null=True)

class FeeAssessmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class FeeAssessmentDetailResponseData(serializers.Serializer):
    assessment = FeeAssessmentDisplaySerializer()

class FeeAssessmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeAssessmentDetailResponseData(allow_null=True)

class FeeAssessmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = FeeAssessmentMinimalSerializer(many=True)

class FeeAssessmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeAssessmentListResponseData()

class FeeAssessmentMarkOverdueResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

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

class FeeAssessmentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Fees - Assessments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="enrollment_id", type=int, description="Filter by enrollment ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by payment status", required=False),
        ],
        responses={200: FeeAssessmentListResponseSerializer},
        description="List fee assessments (students/parents see their own, staff see all)."
    )
    def get(self, request):
        user = request.user
        enrollment_id = request.query_params.get("enrollment_id")
        status_filter = request.query_params.get("status")

        if user.is_staff or can_manage_fee_assessment(user):
            queryset = FeeAssessment.objects.all().select_related('enrollment', 'fee_structure', 'term')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = FeeAssessment.objects.filter(enrollment__student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = FeeAssessment.objects.filter(enrollment__student_id__in=child_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if enrollment_id:
            queryset = queryset.filter(enrollment_id=enrollment_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, FeeAssessmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Fee assessments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Fees - Assessments"],
        request=FeeAssessmentCreateSerializer,
        responses={201: FeeAssessmentCreateResponseSerializer, 400: FeeAssessmentCreateResponseSerializer, 403: FeeAssessmentCreateResponseSerializer},
        description="Create a fee assessment (admin/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_fee_assessment(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = FeeAssessmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            assessment = serializer.save()
            return Response({
                "status": True,
                "message": "Fee assessment created.",
                "data": {
                    "id": assessment.id,
                    "enrollment": assessment.enrollment.id,
                    "amount": assessment.amount,
                    "due_date": assessment.due_date,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FeeAssessmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, assessment_id):
        try:
            return FeeAssessment.objects.select_related('enrollment', 'fee_structure', 'term').get(id=assessment_id)
        except FeeAssessment.DoesNotExist:
            return None

    @extend_schema(
        tags=["Fees - Assessments"],
        responses={200: FeeAssessmentDetailResponseSerializer, 404: FeeAssessmentDetailResponseSerializer, 403: FeeAssessmentDetailResponseSerializer},
        description="Retrieve a single fee assessment by ID."
    )
    def get(self, request, assessment_id):
        assessment = self.get_object(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Fee assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_fee_assessment(request.user, assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = FeeAssessmentDisplaySerializer(assessment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Fee assessment retrieved.",
            "data": {"assessment": data}
        })

    @extend_schema(
        tags=["Fees - Assessments"],
        request=FeeAssessmentUpdateSerializer,
        responses={200: FeeAssessmentUpdateResponseSerializer, 400: FeeAssessmentUpdateResponseSerializer, 403: FeeAssessmentUpdateResponseSerializer},
        description="Update a fee assessment (admin/accounting only)."
    )
    @transaction.atomic
    def put(self, request, assessment_id):
        return self._update(request, assessment_id, partial=False)

    @extend_schema(
        tags=["Fees - Assessments"],
        request=FeeAssessmentUpdateSerializer,
        responses={200: FeeAssessmentUpdateResponseSerializer, 400: FeeAssessmentUpdateResponseSerializer, 403: FeeAssessmentUpdateResponseSerializer},
        description="Partially update a fee assessment."
    )
    @transaction.atomic
    def patch(self, request, assessment_id):
        return self._update(request, assessment_id, partial=True)

    def _update(self, request, assessment_id, partial):
        if not can_manage_fee_assessment(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        assessment = self.get_object(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Fee assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = FeeAssessmentUpdateSerializer(assessment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = FeeAssessmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Fee assessment updated.",
                "data": {"assessment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Fees - Assessments"],
        responses={200: FeeAssessmentDeleteResponseSerializer, 403: FeeAssessmentDeleteResponseSerializer, 404: FeeAssessmentDeleteResponseSerializer},
        description="Delete a fee assessment (admin/accounting only)."
    )
    @transaction.atomic
    def delete(self, request, assessment_id):
        if not can_manage_fee_assessment(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        assessment = self.get_object(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Fee assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = FeeAssessmentService.delete_assessment(assessment)
        if success:
            return Response({
                "status": True,
                "message": "Fee assessment deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete fee assessment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeeAssessmentMarkOverdueView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Fees - Assessments"],
        responses={200: FeeAssessmentMarkOverdueResponseSerializer, 403: FeeAssessmentMarkOverdueResponseSerializer},
        description="Mark overdue assessments (admin/accounting only, run as cron)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_fee_assessment(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        count = FeeAssessmentService.mark_overdue()
        return Response({
            "status": True,
            "message": f"{count} assessments marked as overdue.",
            "data": None
        })