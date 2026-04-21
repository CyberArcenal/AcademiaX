from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..models.product import Product
from ..models.category import Category

class ProductService:
    """Service for Product model operations"""

    @staticmethod
    def create_product(
        name: str,
        category: Category,
        price: Decimal,
        cost: Decimal = Decimal('0'),
        stock_quantity: int = 0,
        is_available: bool = True,
        preparation_time_minutes: int = 5,
        is_vegetarian: bool = False,
        is_gluten_free: bool = False,
        description: str = "",
        image_url: str = ""
    ) -> Product:
        try:
            with transaction.atomic():
                product = Product(
                    name=name,
                    category=category,
                    description=description,
                    price=price,
                    cost=cost,
                    stock_quantity=stock_quantity,
                    is_available=is_available,
                    image_url=image_url,
                    preparation_time_minutes=preparation_time_minutes,
                    is_vegetarian=is_vegetarian,
                    is_gluten_free=is_gluten_free
                )
                product.full_clean()
                product.save()
                return product
        except ValidationError as e:
            raise

    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None

    @staticmethod
    def get_products_by_category(category_id: int, only_available: bool = True) -> List[Product]:
        queryset = Product.objects.filter(category_id=category_id)
        if only_available:
            queryset = queryset.filter(is_available=True, stock_quantity__gt=0)
        return queryset

    @staticmethod
    def get_available_products() -> List[Product]:
        return Product.objects.filter(is_available=True, stock_quantity__gt=0)

    @staticmethod
    def update_product(product: Product, update_data: Dict[str, Any]) -> Product:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(product, field):
                        setattr(product, field, value)
                product.full_clean()
                product.save()
                return product
        except ValidationError as e:
            raise

    @staticmethod
    def delete_product(product: Product, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                product.is_available = False
                product.save()
            else:
                product.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_products(query: str, limit: int = 20) -> List[Product]:
        from django.db import models
        return Product.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query)
        )[:limit]

    @staticmethod
    def update_stock(product: Product, quantity_change: int) -> Product:
        """Update stock quantity (positive for restock, negative for sale)"""
        product.stock_quantity += quantity_change
        if product.stock_quantity < 0:
            raise ValidationError("Insufficient stock")
        product.save()
        return product

    @staticmethod
    def check_availability(product: Product, requested_quantity: int) -> bool:
        return product.is_available and product.stock_quantity >= requested_quantity