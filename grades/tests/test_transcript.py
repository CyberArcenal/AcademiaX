from django.test import TestCase
from decimal import Decimal
from datetime import date
from students.models import Student
from grades.models import Transcript
from grades.services.transcript import TranscriptService
from grades.serializers.transcript import (
    TranscriptCreateSerializer,
    TranscriptUpdateSerializer,
    TranscriptDisplaySerializer,
)


class TranscriptModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )

    def test_create_transcript(self):
        transcript = Transcript.objects.create(
            student=self.student,
            cumulative_gwa=Decimal('87.50'),
            total_units_completed=Decimal('60.0'),
            graduation_date=date(2026, 5, 31),
            is_official=False,
            notes="Draft"
        )
        self.assertEqual(transcript.student, self.student)
        self.assertEqual(transcript.cumulative_gwa, Decimal('87.50'))

    def test_str_method(self):
        transcript = Transcript.objects.create(student=self.student)
        expected = f"Transcript - {self.student}"
        self.assertEqual(str(transcript), expected)


class TranscriptServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F")

    def test_create_transcript(self):
        transcript = TranscriptService.create_transcript(
            student=self.student,
            cumulative_gwa=Decimal('89.00'),
            total_units_completed=Decimal('45.0')
        )
        self.assertEqual(transcript.student, self.student)

    def test_get_transcript_by_student(self):
        transcript = Transcript.objects.create(student=self.student)
        fetched = TranscriptService.get_transcript_by_student(self.student.id)
        self.assertEqual(fetched, transcript)

    def test_update_transcript(self):
        transcript = Transcript.objects.create(student=self.student, cumulative_gwa=85)
        updated = TranscriptService.update_transcript(transcript, {"cumulative_gwa": "88.50", "is_official": True})
        self.assertEqual(updated.cumulative_gwa, Decimal('88.50'))
        self.assertTrue(updated.is_official)

    def test_mark_official(self):
        transcript = Transcript.objects.create(student=self.student, is_official=False)
        marked = TranscriptService.mark_official(transcript)
        self.assertTrue(marked.is_official)


class TranscriptSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M")

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "cumulative_gwa": "90.00",
            "total_units_completed": "75.0",
            "graduation_date": "2026-05-31",
            "is_official": False,
            "notes": "Temporary"
        }
        serializer = TranscriptCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        transcript = serializer.save()
        self.assertEqual(transcript.student, self.student)

    def test_update_serializer(self):
        transcript = Transcript.objects.create(student=self.student, cumulative_gwa=85)
        data = {"cumulative_gwa": "86.50", "pdf_url": "http://example.com/transcript.pdf"}
        serializer = TranscriptUpdateSerializer(transcript, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.cumulative_gwa, Decimal('86.50'))

    def test_display_serializer(self):
        transcript = Transcript.objects.create(student=self.student, cumulative_gwa=87)
        serializer = TranscriptDisplaySerializer(transcript)
        self.assertEqual(serializer.data["cumulative_gwa"], "87.00")
        self.assertEqual(serializer.data["student"]["id"], self.student.id)