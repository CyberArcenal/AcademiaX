from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.order_item import OrderItem
from ..models.order import Order
from ..models.product import Product

class OrderItemService:
    """Service for OrderItem model operations"""

    @staticmethod
    def add_item_to_order(
        order: Order,
        product: Product,
        quantity: int = 1,
        special_instructions: str = ""
    ) -> OrderItem:
        try:
            with transaction.atomic():
                # Check if item already exists
                existing = OrderItem.objects.filter(order=order, product=product).first()
                if existing:
                    existing.quantity += quantity
                    existing.save()
                    return existing

                # Create new item
                order_item = OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    special_instructions=special_instructions
                )
                order_item.full_clean()
                order_item.save()
                return order_item
        except ValidationError as e:
            raise

    @staticmethod
    def get_order_item_by_id(item_id: int) -> Optional[OrderItem]:
        try:
            return OrderItem.objects.get(id=item_id)
        except OrderItem.DoesNotExist:
            return None

    @staticmethod
    def get_items_by_order(order_id: int) -> List[OrderItem]:
        return OrderItem.objects.filter(order_id=order_id).select_related('product')

    @staticmethod
    def update_quantity(item: OrderItem, new_quantity: int) -> OrderItem:
        if new_quantity <= 0:
            item.delete()
            return None
        item.quantity = new_quantity
        item.save()
        return item

    @staticmethod
    def remove_item(item: OrderItem) -> bool:
        try:
            item.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def update_subtotal(item: OrderItem) -> Decimal:
        item.subtotal = item.quantity * item.unit_price
        item.save()
        return item.subtotal