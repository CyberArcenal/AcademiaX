from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.author import Author

class AuthorService:
    """Service for Author model operations"""

    @staticmethod
    def create_author(
        first_name: str,
        last_name: str,
        middle_name: str = "",
        biography: str = "",
        birth_date: Optional[date] = None,
        death_date: Optional[date] = None
    ) -> Author:
        try:
            with transaction.atomic():
                author = Author(
                    first_name=first_name.title(),
                    last_name=last_name.title(),
                    middle_name=middle_name.title(),
                    biography=biography,
                    birth_date=birth_date,
                    death_date=death_date
                )
                author.full_clean()
                author.save()
                return author
        except ValidationError as e:
            raise

    @staticmethod
    def get_author_by_id(author_id: int) -> Optional[Author]:
        try:
            return Author.objects.get(id=author_id)
        except Author.DoesNotExist:
            return None

    @staticmethod
    def get_all_authors(limit: int = 100) -> List[Author]:
        return Author.objects.all().order_by('last_name', 'first_name')[:limit]

    @staticmethod
    def update_author(author: Author, update_data: Dict[str, Any]) -> Author:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(author, field):
                        if field in ['first_name', 'last_name', 'middle_name']:
                            value = value.title()
                        setattr(author, field, value)
                author.full_clean()
                author.save()
                return author
        except ValidationError as e:
            raise

    @staticmethod
    def delete_author(author: Author, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                author.is_active = False
                author.save()
            else:
                author.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def search_authors(query: str, limit: int = 20) -> List[Author]:
        from django.db import models
        return Author.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(middle_name__icontains=query)
        )[:limit]