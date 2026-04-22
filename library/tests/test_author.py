from django.test import TestCase
from datetime import date
from library.models import Author
from library.services.author import AuthorService
from library.serializers.author import (
    AuthorCreateSerializer,
    AuthorUpdateSerializer,
    AuthorDisplaySerializer,
)


class AuthorModelTest(TestCase):
    def test_create_author(self):
        author = Author.objects.create(
            first_name="Jose",
            last_name="Rizal",
            middle_name="Protacio",
            biography="National hero of the Philippines",
            birth_date=date(1861, 6, 19),
            death_date=date(1896, 12, 30)
        )
        self.assertEqual(author.first_name, "Jose")
        self.assertEqual(author.last_name, "Rizal")

    def test_str_method(self):
        author = Author.objects.create(first_name="Jose", last_name="Rizal")
        self.assertEqual(str(author), "Rizal, Jose")


class AuthorServiceTest(TestCase):
    def test_create_author(self):
        author = AuthorService.create_author(
            first_name="F. Sionil",
            last_name="Jose",
            biography="Filipino novelist"
        )
        self.assertEqual(author.last_name, "Jose")

    def test_get_all_authors(self):
        Author.objects.create(first_name="Nick", last_name="Joacquin")
        Author.objects.create(first_name="Lualhati", last_name="Bautista")
        authors = AuthorService.get_all_authors()
        self.assertEqual(authors.count(), 2)

    def test_update_author(self):
        author = Author.objects.create(first_name="Old", last_name="Name")
        updated = AuthorService.update_author(author, {"first_name": "New", "biography": "Updated bio"})
        self.assertEqual(updated.first_name, "New")


class AuthorSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "first_name": "Nick",
            "last_name": "Joacquin",
            "birth_date": "1917-05-04"
        }
        serializer = AuthorCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        author = serializer.save()
        self.assertEqual(author.last_name, "Joacquin")

    def test_update_serializer(self):
        author = Author.objects.create(first_name="Old", last_name="Author")
        data = {"first_name": "Updated", "biography": "New bio"}
        serializer = AuthorUpdateSerializer(author, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.first_name, "Updated")

    def test_display_serializer(self):
        author = Author.objects.create(first_name="Display", last_name="Test")
        serializer = AuthorDisplaySerializer(author)
        self.assertEqual(serializer.data["first_name"], "Display")