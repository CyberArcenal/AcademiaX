import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from fees.models import Payment
from fees.serializers.payment import (
    PaymentMinimalSerializer,
    PaymentCreateSerializer,
    PaymentUpdateSerializer,
    PaymentDisplaySerializer,
)
from fees.services.payment import PaymentService
from fees.services.fee_assessment import FeeAssessmentService

logger = logging.getLogger(__name__)

def can_view_payment(user, payment):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return payment.assessment.enrollment.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return payment.assessment.enrollment.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role in ['ADMIN', 'ACCOUNTING', 'REGISTRAR']:
        return True
    return False

def can_manage_payment(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'ACCOUNTING', 'CASHIER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class PaymentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    assessment = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reference_number = serializers.CharField()

class PaymentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PaymentCreateResponseData(allow_null=True)

class PaymentUpdateResponseData(serializers.Serializer):
    payment = PaymentDisplaySerializer()

class PaymentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PaymentUpdateResponseData(allow_null=True)

class PaymentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class PaymentDetailResponseData(serializers.Serializer):
    payment = PaymentDisplaySerializer()

class PaymentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PaymentDetailResponseData(allow_null=True)

class PaymentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PaymentMinimalSerializer(many=True)

class PaymentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PaymentListResponseData()

class PaymentVerifyResponseData(serializers.Serializer):
    payment = PaymentDisplaySerializer()

class PaymentVerifyResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PaymentVerifyResponseData()

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

class PaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Fees - Payments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="assessment_id", type=int, description="Filter by assessment ID", required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID (via assessment)", required=False),
        ],
        responses={200: PaymentListResponseSerializer},
        description="List payments (students/parents see their own, staff see all)."
    )
    def get(self, request):
        user = request.user
        assessment_id = request.query_params.get("assessment_id")
        student_id = request.query_params.get("student_id")

        if user.is_staff or can_manage_payment(user):
            queryset = Payment.objects.all().select_related('assessment', 'received_by')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = Payment.objects.filter(assessment__enrollment__student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = Payment.objects.filter(assessment__enrollment__student_id__in=child_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        if student_id:
            queryset = queryset.filter(assessment__enrollment__student_id=student_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, PaymentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Payments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Fees - Payments"],
        request=PaymentCreateSerializer,
        responses={201: PaymentCreateResponseSerializer, 400: PaymentCreateResponseSerializer, 403: PaymentCreateResponseSerializer},
        description="Record a payment (cashier/accounting/admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_payment(request.user):
            return Response({
                "status": False,
                "message": "Cashier, accounting, or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Add received_by from current user
        data = request.data.copy()
        data['received_by_id'] = request.user.id
        serializer = PaymentCreateSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save()
            return Response({
                "status": True,
                "message": "Payment recorded.",
                "data": {
                    "id": payment.id,
                    "assessment": payment.assessment.id,
                    "amount": payment.amount,
                    "reference_number": payment.reference_number,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, payment_id):
        try:
            return Payment.objects.select_related('assessment', 'received_by').get(id=payment_id)
        except Payment.DoesNotExist:
            return None

    @extend_schema(
        tags=["Fees - Payments"],
        responses={200: PaymentDetailResponseSerializer, 404: PaymentDetailResponseSerializer, 403: PaymentDetailResponseSerializer},
        description="Retrieve a single payment by ID."
    )
    def get(self, request, payment_id):
        payment = self.get_object(payment_id)
        if not payment:
            return Response({
                "status": False,
                "message": "Payment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_payment(request.user, payment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = PaymentDisplaySerializer(payment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Payment retrieved.",
            "data": {"payment": data}
        })

    @extend_schema(
        tags=["Fees - Payments"],
        request=PaymentUpdateSerializer,
        responses={200: PaymentUpdateResponseSerializer, 400: PaymentUpdateResponseSerializer, 403: PaymentUpdateResponseSerializer},
        description="Update a payment (e.g., mark verified)."
    )
    @transaction.atomic
    def put(self, request, payment_id):
        return self._update(request, payment_id, partial=False)

    @extend_schema(
        tags=["Fees - Payments"],
        request=PaymentUpdateSerializer,
        responses={200: PaymentUpdateResponseSerializer, 400: PaymentUpdateResponseSerializer, 403: PaymentUpdateResponseSerializer},
        description="Partially update a payment."
    )
    @transaction.atomic
    def patch(self, request, payment_id):
        return self._update(request, payment_id, partial=True)

    def _update(self, request, payment_id, partial):
        if not can_manage_payment(request.user):
            return Response({
                "status": False,
                "message": "Cashier, accounting, or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        payment = self.get_object(payment_id)
        if not payment:
            return Response({
                "status": False,
                "message": "Payment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = PaymentUpdateSerializer(payment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PaymentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Payment updated.",
                "data": {"payment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Fees - Payments"],
        responses={200: PaymentDeleteResponseSerializer, 403: PaymentDeleteResponseSerializer, 404: PaymentDeleteResponseSerializer},
        description="Delete a payment (admin only, restores assessment balance)."
    )
    @transaction.atomic
    def delete(self, request, payment_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        payment = self.get_object(payment_id)
        if not payment:
            return Response({
                "status": False,
                "message": "Payment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = PaymentService.delete_payment(payment)
        if success:
            return Response({
                "status": True,
                "message": "Payment deleted and assessment balance restored.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete payment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Fees - Payments"],
        responses={200: PaymentVerifyResponseSerializer, 403: PaymentVerifyResponseSerializer, 404: PaymentVerifyResponseSerializer},
        description="Verify a payment (mark as verified)."
    )
    @transaction.atomic
    def post(self, request, payment_id):
        if not can_manage_payment(request.user):
            return Response({
                "status": False,
                "message": "Cashier, accounting, or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        payment = PaymentService.get_payment_by_id(payment_id)
        if not payment:
            return Response({
                "status": False,
                "message": "Payment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if payment.is_verified:
            return Response({
                "status": False,
                "message": "Payment already verified.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = PaymentService.verify_payment(payment)
        data = PaymentDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Payment verified.",
            "data": {"payment": data}
        })