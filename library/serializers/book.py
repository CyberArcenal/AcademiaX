from rest_framework import serializers
from library.models import Book
from .author import AuthorMinimalSerializer
from .publisher import PublisherMinimalSerializer


class BookMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for books."""

    authors = AuthorMinimalSerializer(many=True, read_only=True)
    publisher = PublisherMinimalSerializer(read_only=True)

    class Meta:
        model = Book
        fields = ["id", "title", "isbn", "authors", "publisher", "publication_year", "total_copies"]
        read_only_fields = fields


class BookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a book."""

    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), many=True, write_only=True
    )
    publisher_id = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(), source="publisher"
    )

    class Meta:
        model = Book
        fields = [
            "isbn", "title", "subtitle", "publisher_id", "publication_year", "edition",
            "language", "pages", "description", "cover_image_url", "dewey_decimal",
            "subject", "total_copies", "available_copies", "author_ids"
        ]

    def create(self, validated_data) -> Book:
        from library.services.book import BookService

        authors = validated_data.pop('author_ids')
        return BookService.create_book(authors=authors, **validated_data)


class BookUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a book."""

    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Book
        fields = [
            "title", "subtitle", "edition", "language", "pages", "description",
            "cover_image_url", "dewey_decimal", "subject", "total_copies",
            "available_copies", "author_ids"
        ]

    def update(self, instance, validated_data) -> Book:
        from library.services.book import BookService

        authors = validated_data.pop('author_ids', None)
        if authors is not None:
            validated_data['authors'] = authors
        return BookService.update_book(instance, validated_data)


class BookDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a book."""

    authors = AuthorMinimalSerializer(many=True, read_only=True)
    publisher = PublisherMinimalSerializer(read_only=True)

    class Meta:
        model = Book
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]