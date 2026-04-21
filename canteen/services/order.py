from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.order import Order
from ..models.order_item import OrderItem
from ..models.product import Product
from ...students.models.student import Student
from ...users.models import User
from ...common.enums.canteen import OrderStatus, OrderType

class OrderService:
    """Service for Order model operations"""

    @staticmethod
    def generate_order_number() -> str:
        """Generate a unique order number"""
        import random
        import string
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"ORD-{timestamp}-{random_str}"

    @staticmethod
    def create_order(
        order_type: str = OrderType.DINE_IN,
        student: Optional[Student] = None,
        user: Optional[User] = None,
        notes: str = "",
        created_by: Optional[User] = None
    ) -> Order:
        try:
            with transaction.atomic():
                order = Order(
                    student=student,
                    user=user,
                    order_number=OrderService.generate_order_number(),
                    order_type=order_type,
                    status=OrderStatus.PENDING,
                    total_amount=Decimal('0'),
                    notes=notes,
                    prepared_by=created_by
                )
                order.full_clean()
                order.save()
                return order
        except ValidationError as e:
            raise

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Order]:
        try:
            return Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return None

    @staticmethod
    def get_order_by_number(order_number: str) -> Optional[Order]:
        try:
            return Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return None

    @staticmethod
    def get_orders_by_student(student_id: int, limit: int = 20) -> List[Order]:
        return Order.objects.filter(student_id=student_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_orders_by_user(user_id: int, limit: int = 20) -> List[Order]:
        return Order.objects.filter(user_id=user_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_pending_orders() -> List[Order]:
        return Order.objects.filter(status=OrderStatus.PENDING).order_by('created_at')

    @staticmethod
    def update_order_status(order: Order, status: str, prepared_by: Optional[User] = None) -> Order:
        order.status = status
        if status == OrderStatus.READY:
            order.served_at = timezone.now()
        if prepared_by:
            order.prepared_by = prepared_by
        order.save()
        return order

    @staticmethod
    def cancel_order(order: Order, reason: str) -> Order:
        order.status = OrderStatus.CANCELLED
        order.cancelled_reason = reason
        order.save()
        # Restore stock for each item
        for item in order.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
        return order

    @staticmethod
    def recalculate_total(order: Order) -> Decimal:
        total = sum(item.subtotal for item in order.items.all())
        order.total_amount = total
        order.save()
        return total

    @staticmethod
    def delete_order(order: Order) -> bool:
        try:
            order.delete()
            return True
        except Exception:
            return False