import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers
from django.core.exceptions import ValidationError
from canteen.models import Wallet, WalletTransaction
from canteen.serializers.wallet import (
    WalletMinimalSerializer,
    WalletCreateSerializer,
    WalletUpdateSerializer,
    WalletDisplaySerializer,
    WalletTransactionMinimalSerializer,
    WalletTransactionCreateSerializer,
    WalletTransactionUpdateSerializer,
    WalletTransactionDisplaySerializer,
)
from canteen.services.wallet import WalletService, WalletTransactionService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_wallet(user, wallet):
    if user.is_staff:
        return True
    if wallet.user == user:
        return True
    return False

def can_process_wallet_transaction(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN' or user.role == 'CASHIER')

# ----------------------------------------------------------------------
# Response serializers for Wallet
# ----------------------------------------------------------------------

class WalletCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.IntegerField()
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)

class WalletCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletCreateResponseData(allow_null=True)

class WalletUpdateResponseData(serializers.Serializer):
    wallet = WalletDisplaySerializer()

class WalletUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletUpdateResponseData(allow_null=True)

class WalletDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class WalletDetailResponseData(serializers.Serializer):
    wallet = WalletDisplaySerializer()

class WalletDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletDetailResponseData(allow_null=True)

class WalletListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = WalletMinimalSerializer(many=True)

class WalletListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletListResponseData()

# ----------------------------------------------------------------------
# Response serializers for WalletTransaction
# ----------------------------------------------------------------------

class WalletTransactionCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    wallet = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = serializers.CharField()

class WalletTransactionCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletTransactionCreateResponseData(allow_null=True)

class WalletTransactionUpdateResponseData(serializers.Serializer):
    transaction = WalletTransactionDisplaySerializer()

class WalletTransactionUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletTransactionUpdateResponseData(allow_null=True)

class WalletTransactionDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class WalletTransactionDetailResponseData(serializers.Serializer):
    transaction = WalletTransactionDisplaySerializer()

class WalletTransactionDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletTransactionDetailResponseData(allow_null=True)

class WalletTransactionListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = WalletTransactionMinimalSerializer(many=True)

class WalletTransactionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = WalletTransactionListResponseData()

# Load/Deduct serializers
class WalletLoadSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    reference = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)

class WalletDeductSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    reference = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)

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
# Wallet Views
# ----------------------------------------------------------------------

class WalletListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Wallet"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: WalletListResponseSerializer},
        description="List wallets (admin only)."
    )
    def get(self, request):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        wallets = Wallet.objects.all().select_related('user')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(wallets, request)
        data = wrap_paginated_data(paginator, page, request, WalletMinimalSerializer)
        return Response({
            "status": True,
            "message": "Wallets retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Wallet"],
        request=WalletCreateSerializer,
        responses={201: WalletCreateResponseSerializer, 400: WalletCreateResponseSerializer, 403: WalletCreateResponseSerializer},
        description="Create a wallet for a user (usually auto-created, but can be manual)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = WalletCreateSerializer(data=request.data)
        if serializer.is_valid():
            wallet = serializer.save()
            return Response({
                "status": True,
                "message": "Wallet created.",
                "data": {
                    "id": wallet.id,
                    "user": wallet.user.id,
                    "balance": wallet.balance,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class WalletDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, wallet_id):
        try:
            return Wallet.objects.select_related('user').get(id=wallet_id)
        except Wallet.DoesNotExist:
            return None

    @extend_schema(
        tags=["Canteen - Wallet"],
        responses={200: WalletDetailResponseSerializer, 404: WalletDetailResponseSerializer, 403: WalletDetailResponseSerializer},
        description="Retrieve a wallet by ID (owner or admin)."
    )
    def get(self, request, wallet_id):
        wallet = self.get_object(wallet_id)
        if not wallet:
            return Response({
                "status": False,
                "message": "Wallet not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_wallet(request.user, wallet):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = WalletDisplaySerializer(wallet, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Wallet retrieved.",
            "data": {"wallet": data}
        })

    @extend_schema(
        tags=["Canteen - Wallet"],
        request=WalletUpdateSerializer,
        responses={200: WalletUpdateResponseSerializer, 400: WalletUpdateResponseSerializer, 403: WalletUpdateResponseSerializer},
        description="Update a wallet (admin only, but balance not directly updatable)."
    )
    @transaction.atomic
    def put(self, request, wallet_id):
        return self._update(request, wallet_id, partial=False)

    @extend_schema(
        tags=["Canteen - Wallet"],
        request=WalletUpdateSerializer,
        responses={200: WalletUpdateResponseSerializer, 400: WalletUpdateResponseSerializer, 403: WalletUpdateResponseSerializer},
        description="Partially update a wallet (admin only)."
    )
    @transaction.atomic
    def patch(self, request, wallet_id):
        return self._update(request, wallet_id, partial=True)

    def _update(self, request, wallet_id, partial):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        wallet = self.get_object(wallet_id)
        if not wallet:
            return Response({
                "status": False,
                "message": "Wallet not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = WalletUpdateSerializer(wallet, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = WalletDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Wallet updated.",
                "data": {"wallet": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Canteen - Wallet"],
        responses={200: WalletDeleteResponseSerializer, 403: WalletDeleteResponseSerializer, 404: WalletDeleteResponseSerializer},
        description="Delete a wallet (admin only)."
    )
    @transaction.atomic
    def delete(self, request, wallet_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        wallet = self.get_object(wallet_id)
        if not wallet:
            return Response({
                "status": False,
                "message": "Wallet not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Hard delete wallet (cascade to transactions)
        wallet.delete()
        return Response({
            "status": True,
            "message": "Wallet deleted.",
            "data": None
        })


class MyWalletView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Wallet"],
        responses={200: WalletDetailResponseSerializer, 404: WalletDetailResponseSerializer},
        description="Get the authenticated user's wallet."
    )
    def get(self, request):
        wallet = WalletService.get_wallet_by_user(request.user.id)
        if not wallet:
            return Response({
                "status": False,
                "message": "Wallet not found for this user.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = WalletDisplaySerializer(wallet, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Wallet retrieved.",
            "data": {"wallet": data}
        })


class WalletLoadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Wallet"],
        request=WalletLoadSerializer,
        responses={200: WalletDetailResponseSerializer, 400: WalletDetailResponseSerializer, 403: WalletDetailResponseSerializer},
        description="Load funds into wallet (cashier/admin only)."
    )
    @transaction.atomic
    def post(self, request, wallet_id):
        if not can_process_wallet_transaction(request.user):
            return Response({
                "status": False,
                "message": "Cashier or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        wallet = WalletService.get_wallet_by_id(wallet_id)
        if not wallet:
            return Response({
                "status": False,
                "message": "Wallet not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = WalletLoadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        amount = serializer.validated_data['amount']
        reference = serializer.validated_data.get('reference', '')
        remarks = serializer.validated_data.get('remarks', '')
        updated_wallet = WalletService.add_balance(wallet, amount, reference, remarks, request.user)
        data = WalletDisplaySerializer(updated_wallet, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Wallet loaded successfully.",
            "data": {"wallet": data}
        })


class WalletDeductView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Wallet"],
        request=WalletDeductSerializer,
        responses={200: WalletDetailResponseSerializer, 400: WalletDetailResponseSerializer, 403: WalletDetailResponseSerializer},
        description="Deduct funds from wallet (cashier/admin only)."
    )
    @transaction.atomic
    def post(self, request, wallet_id):
        if not can_process_wallet_transaction(request.user):
            return Response({
                "status": False,
                "message": "Cashier or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        wallet = WalletService.get_wallet_by_id(wallet_id)
        if not wallet:
            return Response({
                "status": False,
                "message": "Wallet not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = WalletDeductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        amount = serializer.validated_data['amount']
        reference = serializer.validated_data.get('reference', '')
        remarks = serializer.validated_data.get('remarks', '')
        try:
            updated_wallet = WalletService.deduct_balance(wallet, amount, reference, remarks, request.user)
        except ValidationError as e:
            return Response({
                "status": False,
                "message": str(e),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        data = WalletDisplaySerializer(updated_wallet, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Wallet deducted successfully.",
            "data": {"wallet": data}
        })


# ----------------------------------------------------------------------
# WalletTransaction Views
# ----------------------------------------------------------------------

class WalletTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Wallet Transactions"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="wallet_id", type=int, description="Filter by wallet ID", required=False),
        ],
        responses={200: WalletTransactionListResponseSerializer},
        description="List wallet transactions (owner or admin)."
    )
    def get(self, request):
        user = request.user
        wallet_id = request.query_params.get("wallet_id")
        if wallet_id:
            wallet = WalletService.get_wallet_by_id(wallet_id)
            if not wallet:
                return Response({
                    "status": False,
                    "message": "Wallet not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
            if not can_manage_wallet(user, wallet):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            transactions = WalletTransactionService.get_transactions_by_user(wallet.user.id)
        elif user.is_staff:
            transactions = WalletTransaction.objects.all().select_related('wallet', 'processed_by').order_by('-created_at')
        else:
            wallet = WalletService.get_wallet_by_user(user.id)
            if not wallet:
                transactions = []
            else:
                transactions = wallet.transactions.all().select_related('processed_by').order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(transactions, request)
        data = wrap_paginated_data(paginator, page, request, WalletTransactionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Wallet transactions retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Wallet Transactions"],
        request=WalletTransactionCreateSerializer,
        responses={201: WalletTransactionCreateResponseSerializer, 400: WalletTransactionCreateResponseSerializer, 403: WalletTransactionCreateResponseSerializer},
        description="Create a wallet transaction (admin only, typically via load/deduct)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = WalletTransactionCreateSerializer(data=request.data)
        if serializer.is_valid():
            transaction_obj = serializer.save()
            return Response({
                "status": True,
                "message": "Transaction created.",
                "data": {
                    "id": transaction_obj.id,
                    "wallet": transaction_obj.wallet.id,
                    "amount": transaction_obj.amount,
                    "transaction_type": transaction_obj.transaction_type,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class WalletTransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, transaction_id):
        try:
            return WalletTransaction.objects.select_related('wallet', 'processed_by').get(id=transaction_id)
        except WalletTransaction.DoesNotExist:
            return None

    @extend_schema(
        tags=["Canteen - Wallet Transactions"],
        responses={200: WalletTransactionDetailResponseSerializer, 404: WalletTransactionDetailResponseSerializer, 403: WalletTransactionDetailResponseSerializer},
        description="Retrieve a single wallet transaction by ID."
    )
    def get(self, request, transaction_id):
        transaction_obj = self.get_object(transaction_id)
        if not transaction_obj:
            return Response({
                "status": False,
                "message": "Transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_wallet(request.user, transaction_obj.wallet):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = WalletTransactionDisplaySerializer(transaction_obj, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Transaction retrieved.",
            "data": {"transaction": data}
        })

    @extend_schema(
        tags=["Canteen - Wallet Transactions"],
        request=WalletTransactionUpdateSerializer,
        responses={200: WalletTransactionUpdateResponseSerializer, 400: WalletTransactionUpdateResponseSerializer, 403: WalletTransactionUpdateResponseSerializer},
        description="Update a wallet transaction (e.g., remarks)."
    )
    @transaction.atomic
    def put(self, request, transaction_id):
        return self._update(request, transaction_id, partial=False)

    @extend_schema(
        tags=["Canteen - Wallet Transactions"],
        request=WalletTransactionUpdateSerializer,
        responses={200: WalletTransactionUpdateResponseSerializer, 400: WalletTransactionUpdateResponseSerializer, 403: WalletTransactionUpdateResponseSerializer},
        description="Partially update a wallet transaction."
    )
    @transaction.atomic
    def patch(self, request, transaction_id):
        return self._update(request, transaction_id, partial=True)

    def _update(self, request, transaction_id, partial):
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
        serializer = WalletTransactionUpdateSerializer(transaction_obj, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = WalletTransactionDisplaySerializer(updated, context={"request": request}).data
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
        tags=["Canteen - Wallet Transactions"],
        responses={200: WalletTransactionDeleteResponseSerializer, 403: WalletTransactionDeleteResponseSerializer, 404: WalletTransactionDeleteResponseSerializer},
        description="Delete a wallet transaction (admin only)."
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
        transaction_obj.delete()
        return Response({
            "status": True,
            "message": "Transaction deleted.",
            "data": None
        })