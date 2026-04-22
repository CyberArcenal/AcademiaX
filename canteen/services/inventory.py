from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from canteen.models.inventory import InventoryLog
from canteen.models.product import Product
from users.models.user import User



class InventoryLogService:
    """Service for InventoryLog model operations"""

    @staticmethod
    def create_log(
        product: Product,
        quantity_change: int,
        reason: str,
        notes: str = "",
        recorded_by: Optional[User] = None
    ) -> InventoryLog:
        try:
            with transaction.atomic():
                new_quantity = product.stock_quantity + quantity_change
                if new_quantity < 0:
                    raise ValidationError("Stock cannot be negative")

                log = InventoryLog(
                    product=product,
                    quantity_change=quantity_change,
                    new_quantity=new_quantity,
                    reason=reason,
                    notes=notes,
                    recorded_by=recorded_by
                )
                log.full_clean()
                log.save()

                # Update product stock
                product.stock_quantity = new_quantity
                product.save()
                return log
        except ValidationError as e:
            raise

    @staticmethod
    def get_log_by_id(log_id: int) -> Optional[InventoryLog]:
        try:
            return InventoryLog.objects.get(id=log_id)
        except InventoryLog.DoesNotExist:
            return None

    @staticmethod
    def get_logs_by_product(product_id: int, limit: int = 50) -> List[InventoryLog]:
        return InventoryLog.objects.filter(product_id=product_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_low_stock_products(threshold: int = 10) -> List[Product]:
        return Product.objects.filter(stock_quantity__lte=threshold, is_available=True)