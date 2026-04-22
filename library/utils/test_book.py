from django.test import TestCase
from datetime import date
from library.models import Author, Publisher, Book
from library.services.book import BookService
from library.serializers.book import (
    BookCreateSerializer,
    BookUpdateSerializer,
    BookDisplaySerializer,
)


class BookModelTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="Jose", last_name="Rizal")
        self.publisher = Publisher.objects.create(name="Anvil Publishing")

    def test_create_book(self):
        book = Book.objects.create(
            isbn="978-971-27-0000-0",
            title="Noli Me Tangere",
            publisher=self.publisher,
            publication_year=1887,
            language="Filipino",
            pages=400,
            total_copies=10,
            available_copies=10
        )
        book.authors.add(self.author)
        self.assertEqual(book.title, "Noli Me Tangere")
        self.assertEqual(book.isbn, "978-971-27-0000-0")

    def test_str_method(self):
        book = Book.objects.create(title="El Filibusterismo", publisher=self.publisher, publication_year=1891)
        self.assertEqual(str(book), "El Filibusterismo (978-971-27-0000-0)")


class BookServiceTest(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(first_name="Jose", last_name="Rizal")
        self.author2 = Author.objects.create(first_name="F. Sionil", last_name="Jose")
        self.publisher = Publisher.objects.create(name="UP Press")

    def test_create_book(self):
        book = BookService.create_book(
            isbn="978-971-27-0001-7",
            title="The Pretenders",
            publisher=self.publisher,
            publication_year=1962,
            authors=[self.author2],
            total_copies=5,
            available_copies=5
        )
        self.assertEqual(book.title, "The Pretenders")
        self.assertEqual(book.authors.count(), 1)

    def test_get_book_by_isbn(self):
        created = Book.objects.create(isbn="1234567890", title="Test", publisher=self.publisher, publication_year=2025)
        fetched = BookService.get_book_by_isbn("1234567890")
        self.assertEqual(fetched, created)

    def test_update_copies_count(self):
        book = Book.objects.create(isbn="1111", title="Test", publisher=self.publisher, publication_year=2025, total_copies=0, available_copies=0)
        # Create copies (we need BookCopy service, but for this test, we'll just update manually)
        book.total_copies = 5
        book.available_copies = 3
        book.save()
        updated = BookService.update_copies_count(book)
        self.assertEqual(updated.total_copies, 5)

    def test_search_books(self):
        Book.objects.create(isbn="1111", title="Python Programming", publisher=self.publisher, publication_year=2025)
        Book.objects.create(isbn="2222", title="Django Guide", publisher=self.publisher, publication_year=2025)
        results = BookService.search_books("Python")
        self.assertEqual(results.count(), 1)


class BookSerializerTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="Jose", last_name="Rizal")
        self.publisher = Publisher.objects.create(name="Anvil")

    def test_create_serializer_valid(self):
        data = {
            "isbn": "978-971-27-0002-4",
            "title": "Poems of Rizal",
            "publisher_id": self.publisher.id,
            "publication_year": 1880,
            "author_ids": [self.author.id],
            "total_copies": 3
        }
        serializer = BookCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        book = serializer.save()
        self.assertEqual(book.publisher, self.publisher)
        self.assertEqual(book.authors.count(), 1)

    def test_update_serializer(self):
        book = Book.objects.create(isbn="1234", title="Old Title", publisher=self.publisher, publication_year=2025)
        data = {"title": "New Title", "description": "Updated description"}
        serializer = BookUpdateSerializer(book, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "New Title")

    def test_display_serializer(self):
        book = Book.objects.create(isbn="5678", title="Display", publisher=self.publisher, publication_year=2025)
        serializer = BookDisplaySerializer(book)
        self.assertEqual(serializer.data["title"], "Display")
        self.assertEqual(serializer.data["publisher"]["id"], self.publisher.id)