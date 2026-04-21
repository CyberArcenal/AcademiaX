import logging

logger = logging.getLogger(__name__)


class BookCopyStateTransitionService:
    """Handles side effects of book copy state changes."""

    @staticmethod
    def handle_creation(copy):
        """When a new copy is created, update book total copies."""
        from library.services.book import BookService
        BookService.update_copies_count(copy.book)
        logger.info(f"Added copy {copy.id} to book {copy.book.id}, updated total copies")

    @staticmethod
    def handle_changes(instance, changes):
        if 'status' in changes:
            BookCopyStateTransitionService._handle_status_change(
                instance, changes['status']['old'], changes['status']['new']
            )

    @staticmethod
    def _handle_status_change(copy, old_status, new_status):
        """When copy status changes, update book available copies."""
        from library.services.book import BookService
        BookService.update_copies_count(copy.book)
        logger.info(f"Copy {copy.id} status changed from {old_status} to {new_status}, updated book available copies")