from rest_framework import serializers
from library.models import BookCopy
from library.models.book import Book
from .book import BookMinimalSerializer


class BookCopyMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for book copies."""

    book = BookMinimalSerializer(read_only=True)

    class Meta:
        model = BookCopy
        fields = ["id", "book", "copy_number", "barcode", "status"]
        read_only_fields = fields


class BookCopyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a book copy."""

    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source="book"
    )

    class Meta:
        model = BookCopy
        fields = ["book_id", "copy_number", "barcode", "status", "location", "acquisition_date", "purchase_price", "notes"]

    def create(self, validated_data) -> BookCopy:
        from library.services.copy import BookCopyService

        return BookCopyService.create_copy(**validated_data)


class BookCopyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a book copy."""

    class Meta:
        model = BookCopy
        fields = ["status", "location", "notes"]

    def update(self, instance, validated_data) -> BookCopy:
        from library.services.copy import BookCopyService

        return BookCopyService.update_copy(instance, validated_data)


class BookCopyDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a book copy."""

    book = BookMinimalSerializer(read_only=True)

    class Meta:
        model = BookCopy
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]