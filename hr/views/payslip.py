import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from hr.models import Payslip
from hr.serializers.payslip import (
    PayslipMinimalSerializer,
    PayslipCreateSerializer,
    PayslipUpdateSerializer,
    PayslipDisplaySerializer,
)
from hr.services.payslip import PayslipService

logger = logging.getLogger(__name__)

def can_view_payslip(user, payslip):
    if user.is_staff:
        return True
    if user.role in ['ADMIN', 'HR_MANAGER', 'ACCOUNTING']:
        return True
    if hasattr(user, 'employee_record'):
        return payslip.employee == user.employee_record
    return False

def can_manage_payslip(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class PayslipCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    employee = serializers.IntegerField()
    period = serializers.IntegerField()
    gross_pay = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_pay = serializers.DecimalField(max_digits=12, decimal_places=2)

class PayslipCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayslipCreateResponseData(allow_null=True)

class PayslipUpdateResponseData(serializers.Serializer):
    payslip = PayslipDisplaySerializer()

class PayslipUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayslipUpdateResponseData(allow_null=True)

class PayslipDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class PayslipDetailResponseData(serializers.Serializer):
    payslip = PayslipDisplaySerializer()

class PayslipDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayslipDetailResponseData(allow_null=True)

class PayslipListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PayslipMinimalSerializer(many=True)

class PayslipListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayslipListResponseData()

class PayslipMarkPaidResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayslipDetailResponseData()

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

class PayslipListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Payslips"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="employee_id", type=int, description="Filter by employee ID", required=False),
            OpenApiParameter(name="period_id", type=int, description="Filter by payroll period ID", required=False),
        ],
        responses={200: PayslipListResponseSerializer},
        description="List payslips (admins/hr/accounting see all, employees see their own)."
    )
    def get(self, request):
        user = request.user
        employee_id = request.query_params.get("employee_id")
        period_id = request.query_params.get("period_id")

        if user.is_staff or can_manage_payslip(user):
            queryset = Payslip.objects.all().select_related('employee', 'period')
        else:
            if hasattr(user, 'employee_record'):
                queryset = Payslip.objects.filter(employee=user.employee_record)
            else:
                return Response({
                    "status": False,
                    "message": "Employee record not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if period_id:
            queryset = queryset.filter(period_id=period_id)

        queryset = queryset.order_by('-period__start_date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, PayslipMinimalSerializer)
        return Response({
            "status": True,
            "message": "Payslips retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Payslips"],
        request=PayslipCreateSerializer,
        responses={201: PayslipCreateResponseSerializer, 400: PayslipCreateResponseSerializer, 403: PayslipCreateResponseSerializer},
        description="Generate a payslip for an employee (admin/hr/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_payslip(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = PayslipCreateSerializer(data=request.data)
        if serializer.is_valid():
            payslip = serializer.save()
            return Response({
                "status": True,
                "message": "Payslip generated.",
                "data": {
                    "id": payslip.id,
                    "employee": payslip.employee.id,
                    "period": payslip.period.id,
                    "gross_pay": payslip.gross_pay,
                    "net_pay": payslip.net_pay,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PayslipDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, payslip_id):
        try:
            return Payslip.objects.select_related('employee', 'period').get(id=payslip_id)
        except Payslip.DoesNotExist:
            return None

    @extend_schema(
        tags=["HR - Payslips"],
        responses={200: PayslipDetailResponseSerializer, 404: PayslipDetailResponseSerializer, 403: PayslipDetailResponseSerializer},
        description="Retrieve a single payslip by ID."
    )
    def get(self, request, payslip_id):
        payslip = self.get_object(payslip_id)
        if not payslip:
            return Response({
                "status": False,
                "message": "Payslip not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_payslip(request.user, payslip):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = PayslipDisplaySerializer(payslip, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Payslip retrieved.",
            "data": {"payslip": data}
        })

    @extend_schema(
        tags=["HR - Payslips"],
        request=PayslipUpdateSerializer,
        responses={200: PayslipUpdateResponseSerializer, 400: PayslipUpdateResponseSerializer, 403: PayslipUpdateResponseSerializer},
        description="Update a payslip (e.g., adjust amounts, mark paid)."
    )
    @transaction.atomic
    def put(self, request, payslip_id):
        return self._update(request, payslip_id, partial=False)

    @extend_schema(
        tags=["HR - Payslips"],
        request=PayslipUpdateSerializer,
        responses={200: PayslipUpdateResponseSerializer, 400: PayslipUpdateResponseSerializer, 403: PayslipUpdateResponseSerializer},
        description="Partially update a payslip."
    )
    @transaction.atomic
    def patch(self, request, payslip_id):
        return self._update(request, payslip_id, partial=True)

    def _update(self, request, payslip_id, partial):
        if not can_manage_payslip(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        payslip = self.get_object(payslip_id)
        if not payslip:
            return Response({
                "status": False,
                "message": "Payslip not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = PayslipUpdateSerializer(payslip, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PayslipDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Payslip updated.",
                "data": {"payslip": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["HR - Payslips"],
        responses={200: PayslipDeleteResponseSerializer, 403: PayslipDeleteResponseSerializer, 404: PayslipDeleteResponseSerializer},
        description="Delete a payslip (admin only)."
    )
    @transaction.atomic
    def delete(self, request, payslip_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        payslip = self.get_object(payslip_id)
        if not payslip:
            return Response({
                "status": False,
                "message": "Payslip not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = PayslipService.delete_payslip(payslip)
        if success:
            return Response({
                "status": True,
                "message": "Payslip deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete payslip.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PayslipMarkPaidView(APIView):
    permission_classes = [IsAuthenticated]

    class PaidSerializer(serializers.Serializer):
        payment_date = serializers.DateField()

    @extend_schema(
        tags=["HR - Payslips"],
        request=PaidSerializer,
        responses={200: PayslipMarkPaidResponseSerializer, 400: PayslipMarkPaidResponseSerializer, 403: PayslipMarkPaidResponseSerializer},
        description="Mark a payslip as paid (admin/hr/accounting only)."
    )
    @transaction.atomic
    def post(self, request, payslip_id):
        if not can_manage_payslip(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        payslip = PayslipService.get_payslip_by_id(payslip_id)
        if not payslip:
            return Response({
                "status": False,
                "message": "Payslip not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if payslip.payment_date:
            return Response({
                "status": False,
                "message": "Payslip already marked as paid.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.PaidSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = PayslipService.mark_paid(payslip, serializer.validated_data['payment_date'])
        data = PayslipDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Payslip marked as paid.",
            "data": {"payslip": data}
        })