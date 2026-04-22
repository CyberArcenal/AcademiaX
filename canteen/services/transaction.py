from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, Dict, Any
from decimal import Decimal

from canteen.models.order import Order
from canteen.models.transaction import PaymentTransaction
from common.enums.canteen import OrderStatus, PaymentMethod
from users.models.user import User



class PaymentTransactionService:
    """Service for PaymentTransaction model operations"""

    @staticmethod
    def process_payment(
        order: Order,
        amount_paid: Decimal,
        payment_method: str = PaymentMethod.CASH,
        reference_number: str = "",
        received_by: Optional[User] = None
    ) -> PaymentTransaction:
        try:
            with transaction.atomic():
                if order.status == OrderStatus.CANCELLED:
                    raise ValidationError("Cannot pay for cancelled order")

                change_due = amount_paid - order.total_amount
                if change_due < 0:
                    raise ValidationError("Insufficient payment amount")

                transaction_obj = PaymentTransaction(
                    order=order,
                    amount_paid=amount_paid,
                    change_due=change_due,
                    payment_method=payment_method,
                    reference_number=reference_number,
                    received_by=received_by
                )
                transaction_obj.full_clean()
                transaction_obj.save()

                # Update order status
                order.status = OrderStatus.COMPLETED
                order.save()

                return transaction_obj
        except ValidationError as e:
            raise

    @staticmethod
    def get_transaction_by_id(transaction_id: int) -> Optional[PaymentTransaction]:
        try:
            return PaymentTransaction.objects.get(id=transaction_id)
        except PaymentTransaction.DoesNotExist:
            return None

    @staticmethod
    def get_transaction_by_order(order_id: int) -> Optional[PaymentTransaction]:
        try:
            return PaymentTransaction.objects.get(order_id=order_id)
        except PaymentTransaction.DoesNotExist:
            return None

    @staticmethod
    def get_daily_sales(date) -> Dict[str, Any]:
        from django.db.models import Sum
        transactions = PaymentTransaction.objects.filter(paid_at__date=date)
        total_sales = transactions.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        return {
            'date': date,
            'total_sales': total_sales,
            'transaction_count': transactions.count()
        }