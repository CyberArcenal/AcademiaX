import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from canteen.models import PaymentTransaction, Order
from canteen.serializers.transaction import (
    PaymentTransactionMinimalSerializer,
    PaymentTransactionCreateSerializer,
    PaymentTransactionUpdateSerializer,
    PaymentTransactionDisplaySerializer,
)
from canteen.services.transaction import PaymentTransactionService
from canteen.services.order import OrderService
from common.base.paginations import StandardResultsSetPagination
from django.db import models
logger = logging.getLogger(__name__)

def can_view_transaction(user, transaction_obj):
    if user.is_staff:
        return True
    order = transaction_obj.order
    if order.student and order.student.user == user:
        return True
    if order.user == user:
        return True
    return False

def can_process_payment(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN' or user.role == 'CASHIER')

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TransactionCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    change_due = serializers.DecimalField(max_digits=10, decimal_places=2)

class TransactionCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TransactionCreateResponseData(allow_null=True)

class TransactionUpdateResponseData(serializers.Serializer):
    transaction = PaymentTransactionDisplaySerializer()

class TransactionUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TransactionUpdateResponseData(allow_null=True)

class TransactionDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TransactionDetailResponseData(serializers.Serializer):
    transaction = PaymentTransactionDisplaySerializer()

class TransactionDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TransactionDetailResponseData(allow_null=True)

class TransactionListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PaymentTransactionMinimalSerializer(many=True)

class TransactionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TransactionListResponseData()

class DailySalesResponseData(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()

class DailySalesResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DailySalesResponseData()

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

class PaymentTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Transactions"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="order_id", type=int, description="Filter by order ID", required=False),
        ],
        responses={200: TransactionListResponseSerializer},
        description="List payment transactions (staff see all, users see their own)."
    )
    def get(self, request):
        user = request.user
        order_id = request.query_params.get("order_id")
        if order_id:
            transaction_obj = PaymentTransactionService.get_transaction_by_order(order_id)
            transactions = [transaction_obj] if transaction_obj else []
        elif user.is_staff:
            transactions = PaymentTransaction.objects.all().select_related('order', 'received_by').order_by('-paid_at')
        else:
            # Users see transactions for orders they made
            user_orders = Order.objects.filter(
                models.Q(user=user) | models.Q(student__user=user)
            ).values_list('id', flat=True)
            transactions = PaymentTransaction.objects.filter(order_id__in=user_orders).select_related('order', 'received_by').order_by('-paid_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(transactions, request)
        data = wrap_paginated_data(paginator, page, request, PaymentTransactionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Transactions retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Transactions"],
        request=PaymentTransactionCreateSerializer,
        responses={201: TransactionCreateResponseSerializer, 400: TransactionCreateResponseSerializer, 403: TransactionCreateResponseSerializer},
        description="Process a payment for an order (cashier/admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_process_payment(request.user):
            return Response({
                "status": False,
                "message": "Cashier or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Add received_by from request user
        data = request.data.copy()
        data['received_by_id'] = request.user.id
        serializer = PaymentTransactionCreateSerializer(data=data)
        if serializer.is_valid():
            transaction_obj = serializer.save()
            return Response({
                "status": True,
                "message": "Payment processed.",
                "data": {
                    "id": transaction_obj.id,
                    "order": transaction_obj.order.id,
                    "amount_paid": transaction_obj.amount_paid,
                    "change_due": transaction_obj.change_due,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PaymentTransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, transaction_id):
        try:
            return PaymentTransaction.objects.select_related('order', 'received_by').get(id=transaction_id)
        except PaymentTransaction.DoesNotExist:
            return None

    @extend_schema(
        tags=["Canteen - Transactions"],
        responses={200: TransactionDetailResponseSerializer, 404: TransactionDetailResponseSerializer, 403: TransactionDetailResponseSerializer},
        description="Retrieve a single payment transaction by ID."
    )
    def get(self, request, transaction_id):
        transaction_obj = self.get_object(transaction_id)
        if not transaction_obj:
            return Response({
                "status": False,
                "message": "Transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_transaction(request.user, transaction_obj):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = PaymentTransactionDisplaySerializer(transaction_obj, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Transaction retrieved.",
            "data": {"transaction": data}
        })

    @extend_schema(
        tags=["Canteen - Transactions"],
        request=PaymentTransactionUpdateSerializer,
        responses={200: TransactionUpdateResponseSerializer, 400: TransactionUpdateResponseSerializer, 403: TransactionUpdateResponseSerializer},
        description="Update a transaction (e.g., reference number)."
    )
    @transaction.atomic
    def put(self, request, transaction_id):
        return self._update(request, transaction_id, partial=False)

    @extend_schema(
        tags=["Canteen - Transactions"],
        request=PaymentTransactionUpdateSerializer,
        responses={200: TransactionUpdateResponseSerializer, 400: TransactionUpdateResponseSerializer, 403: TransactionUpdateResponseSerializer},
        description="Partially update a transaction."
    )
    @transaction.atomic
    def patch(self, request, transaction_id):
        return self._update(request, transaction_id, partial=True)

    def _update(self, request, transaction_id, partial):
        if not can_process_payment(request.user):
            return Response({
                "status": False,
                "message": "Cashier or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        transaction_obj = self.get_object(transaction_id)
        if not transaction_obj:
            return Response({
                "status": False,
                "message": "Transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = PaymentTransactionUpdateSerializer(transaction_obj, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PaymentTransactionDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Transaction updated.",
                "data": {"transaction": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Canteen - Transactions"],
        responses={200: TransactionDeleteResponseSerializer, 403: TransactionDeleteResponseSerializer, 404: TransactionDeleteResponseSerializer},
        description="Delete a transaction (admin only)."
    )
    @transaction.atomic
    def delete(self, request, transaction_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        transaction_obj = self.get_object(transaction_id)
        if not transaction_obj:
            return Response({
                "status": False,
                "message": "Transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = PaymentTransactionService.delete_transaction(transaction_obj)
        if success:
            return Response({
                "status": True,
                "message": "Transaction deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete transaction.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailySalesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Transactions"],
        parameters=[
            OpenApiParameter(name="date", type=str, description="Date (YYYY-MM-DD), defaults to today", required=False),
        ],
        responses={200: DailySalesResponseSerializer, 403: DailySalesResponseSerializer},
        description="Get daily sales summary (staff only)."
    )
    def get(self, request):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Staff permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        date_str = request.query_params.get("date")
        from datetime import date, datetime
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Invalid date format. Use YYYY-MM-DD.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = date.today()
        sales_data = PaymentTransactionService.get_daily_sales(target_date)
        return Response({
            "status": True,
            "message": "Daily sales retrieved.",
            "data": {
                "date": target_date,
                "total_sales": sales_data['total_sales'],
                "transaction_count": sales_data['transaction_count'],
            }
        })