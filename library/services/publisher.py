from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.publisher import Publisher

class PublisherService:
    """Service for Publisher model operations"""

    @staticmethod
    def create_publisher(
        name: str,
        address: str = "",
        contact_number: str = "",
        email: str = "",
        website: str = ""
    ) -> Publisher:
        try:
            with transaction.atomic():
                publisher = Publisher(
                    name=name,
                    address=address,
                    contact_number=contact_number,
                    email=email,
                    website=website
                )
                publisher.full_clean()
                publisher.save()
                return publisher
        except ValidationError as e:
            raise

    @staticmethod
    def get_publisher_by_id(publisher_id: int) -> Optional[Publisher]:
        try:
            return Publisher.objects.get(id=publisher_id)
        except Publisher.DoesNotExist:
            return None

    @staticmethod
    def get_publisher_by_name(name: str) -> Optional[Publisher]:
        try:
            return Publisher.objects.get(name__iexact=name)
        except Publisher.DoesNotExist:
            return None

    @staticmethod
    def get_all_publishers() -> List[Publisher]:
        return Publisher.objects.all().order_by('name')

    @staticmethod
    def update_publisher(publisher: Publisher, update_data: Dict[str, Any]) -> Publisher:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(publisher, field):
                        setattr(publisher, field, value)
                publisher.full_clean()
                publisher.save()
                return publisher
        except ValidationError as e:
            raise

    @staticmethod
    def delete_publisher(publisher: Publisher, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                publisher.is_active = False
                publisher.save()
            else:
                publisher.delete()
            return True
        except Exception:
            return False