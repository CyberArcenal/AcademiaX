from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.category import Category
from ...common.enums.canteen import ProductCategory

class CategoryService:
    """Service for Category model operations"""

    @staticmethod
    def create_category(
        name: str,
        display_order: int = 0,
        description: str = ""
    ) -> Category:
        try:
            with transaction.atomic():
                category = Category(
                    name=name,
                    display_order=display_order,
                    description=description
                )
                category.full_clean()
                category.save()
                return category
        except ValidationError as e:
            raise

    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None

    @staticmethod
    def get_category_by_name(name: str) -> Optional[Category]:
        try:
            return Category.objects.get(name=name)
        except Category.DoesNotExist:
            return None

    @staticmethod
    def get_all_categories() -> List[Category]:
        return Category.objects.all()

    @staticmethod
    def update_category(category: Category, update_data: Dict[str, Any]) -> Category:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(category, field):
                        setattr(category, field, value)
                category.full_clean()
                category.save()
                return category
        except ValidationError as e:
            raise

    @staticmethod
    def delete_category(category: Category, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                category.is_active = False
                category.save()
            else:
                category.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def reorder_categories(category_ids_in_order: List[int]) -> bool:
        try:
            with transaction.atomic():
                for idx, cat_id in enumerate(category_ids_in_order, start=1):
                    Category.objects.filter(id=cat_id).update(display_order=idx)
            return True
        except Exception:
            return False