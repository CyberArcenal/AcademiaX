from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.library import BookStatus
from .book import Book

class BookCopy(TimestampedModel, UUIDModel, SoftDeleteModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    copy_number = models.CharField(max_length=20, help_text="e.g., Copy 1, 2025-001")
    barcode = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=BookStatus.choices, default=BookStatus.AVAILABLE)
    location = models.CharField(max_length=100, blank=True, help_text="Shelf or section location")
    acquisition_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['book', 'copy_number']]
        ordering = ['book__title', 'copy_number']

    def __str__(self):
        return f"{self.book.title} - {self.copy_number} ({self.barcode})"