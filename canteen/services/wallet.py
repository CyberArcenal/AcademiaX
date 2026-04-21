from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.wallet import Wallet, WalletTransaction
from ...users.models import User

class WalletService:
    """Service for Wallet model operations"""

    @staticmethod
    def create_wallet(user: User) -> Wallet:
        try:
            with transaction.atomic():
                wallet = Wallet(user=user, balance=Decimal('0'))
                wallet.full_clean()
                wallet.save()
                return wallet
        except ValidationError as e:
            raise

    @staticmethod
    def get_wallet_by_user(user_id: int) -> Optional[Wallet]:
        try:
            return Wallet.objects.get(user_id=user_id)
        except Wallet.DoesNotExist:
            return None

    @staticmethod
    def add_balance(wallet: Wallet, amount: Decimal, reference: str = "", remarks: str = "", processed_by: Optional[User] = None) -> Wallet:
        try:
            with transaction.atomic():
                if amount <= 0:
                    raise ValidationError("Amount must be positive")

                wallet.balance += amount
                wallet.save()

                # Create transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type='LOAD',
                    reference=reference,
                    remarks=remarks,
                    processed_by=processed_by
                )
                return wallet
        except ValidationError as e:
            raise

    @staticmethod
    def deduct_balance(wallet: Wallet, amount: Decimal, reference: str = "", remarks: str = "", processed_by: Optional[User] = None) -> Wallet:
        try:
            with transaction.atomic():
                if amount <= 0:
                    raise ValidationError("Amount must be positive")
                if wallet.balance < amount:
                    raise ValidationError("Insufficient balance")

                wallet.balance -= amount
                wallet.save()

                # Create transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type='DEDUCT',
                    reference=reference,
                    remarks=remarks,
                    processed_by=processed_by
                )
                return wallet
        except ValidationError as e:
            raise

    @staticmethod
    def get_transactions(wallet: Wallet, limit: int = 50) -> List[WalletTransaction]:
        return wallet.transactions.all().order_by('-created_at')[:limit]


class WalletTransactionService:
    """Service for WalletTransaction model operations"""

    @staticmethod
    def get_transaction_by_id(transaction_id: int) -> Optional[WalletTransaction]:
        try:
            return WalletTransaction.objects.get(id=transaction_id)
        except WalletTransaction.DoesNotExist:
            return None

    @staticmethod
    def get_transactions_by_user(user_id: int, limit: int = 50) -> List[WalletTransaction]:
        from ..models.wallet import Wallet
        wallet = Wallet.objects.filter(user_id=user_id).first()
        if wallet:
            return wallet.transactions.all().order_by('-created_at')[:limit]
        return []