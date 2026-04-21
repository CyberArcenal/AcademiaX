from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from .author import Author
from .publisher import Publisher

class Book(TimestampedModel, UUIDModel, SoftDeleteModel):
    isbn = models.CharField(max_length=20, unique=True, help_text="International Standard Book Number")
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=300, blank=True)
    authors = models.ManyToManyField(Author, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name='books')
    publication_year = models.IntegerField()
    edition = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=50, default='English')
    pages = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(blank=True)
    dewey_decimal = models.CharField(max_length=20, blank=True, help_text="Dewey Decimal Classification")
    subject = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=0)
    available_copies = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.isbn})"