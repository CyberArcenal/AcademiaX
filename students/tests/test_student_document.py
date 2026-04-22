from django.test import TestCase
from datetime import date
from users.models import User
from students.models import Student, StudentDocument
from students.services.student_document import StudentDocumentService
from students.serializers.student_document import (
    StudentDocumentCreateSerializer,
    StudentDocumentUpdateSerializer,
    StudentDocumentDisplaySerializer,
)


class StudentDocumentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )

    def test_create_document(self):
        doc = StudentDocument.objects.create(
            student=self.student,
            document_type="PSA_BIRTH",
            title="Birth Certificate",
            file_url="http://example.com/birth.pdf",
            uploaded_by=self.user,
            verified=False
        )
        self.assertEqual(doc.student, self.student)
        self.assertEqual(doc.document_type, "PSA_BIRTH")

    def test_str_method(self):
        doc = StudentDocument.objects.create(student=self.student, title="Test Doc")
        expected = f"{self.student} - Test Doc"
        self.assertEqual(str(doc), expected)


class StudentDocumentServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="registrar", email="reg@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )

    def test_create_document(self):
        doc = StudentDocumentService.create_document(
            student=self.student,
            document_type="REPORT_CARD",
            title="SF9",
            file_url="http://example.com/sf9.pdf",
            uploaded_by=self.user,
            expiry_date=date(2026, 5, 31)
        )
        self.assertEqual(doc.student, self.student)

    def test_verify_document(self):
        doc = StudentDocument.objects.create(student=self.student, document_type="ID_PICTURE", title="2x2", file_url="http://a", uploaded_by=self.user, verified=False)
        verified = StudentDocumentService.verify_document(doc)
        self.assertTrue(verified.verified)
        self.assertIsNotNone(verified.verified_at)


class StudentDocumentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", email="admin2@example.com", password="test")
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "document_type": "GOOD_MORAL",
            "title": "Good Moral Certificate",
            "file_url": "http://example.com/moral.pdf",
            "uploaded_by_id": self.user.id
        }
        serializer = StudentDocumentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        doc = serializer.save()
        self.assertEqual(doc.student, self.student)

    def test_update_serializer(self):
        doc = StudentDocument.objects.create(student=self.student, document_type="OTHER", title="Old", file_url="http://old", uploaded_by=self.user)
        data = {"title": "Updated", "notes": "New notes"}
        serializer = StudentDocumentUpdateSerializer(doc, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "Updated")

    def test_display_serializer(self):
        doc = StudentDocument.objects.create(student=self.student, document_type="PSA_BIRTH", title="Display", file_url="http://disp", uploaded_by=self.user)
        serializer = StudentDocumentDisplaySerializer(doc)
        self.assertEqual(serializer.data["title"], "Display")
        self.assertEqual(serializer.data["student"]["id"], self.student.id)