from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from users.models import User
from students.models import Student
from classes.models import AcademicYear, GradeLevel
from fees.models import Discount, Scholarship
from fees.services.scholarship import ScholarshipService
from fees.serializers.scholarship import (
    ScholarshipCreateSerializer,
    ScholarshipUpdateSerializer,
    ScholarshipDisplaySerializer,
)
from common.enums.fees import DiscountType, ScholarshipType


class ScholarshipModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.discount = Discount.objects.create(
            name="Academic Scholarship",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal('25.00'),
            is_percentage=True
        )

    def test_create_scholarship(self):
        scholarship = Scholarship.objects.create(
            student=self.student,
            discount=self.discount,
            scholarship_type=ScholarshipType.ACADEMIC,
            awarded_date=date(2025, 6, 1),
            expiry_date=date(2026, 5, 31),
            is_renewable=True,
            grantor="School Foundation"
        )
        self.assertEqual(scholarship.student, self.student)
        self.assertEqual(scholarship.discount, self.discount)
        self.assertEqual(scholarship.scholarship_type, ScholarshipType.ACADEMIC)

    def test_str_method(self):
        scholarship = Scholarship.objects.create(
            student=self.student,
            discount=self.discount,
            scholarship_type=ScholarshipType.NEED_BASED
        )
        expected = f"{self.student} - Academic Scholarship"
        self.assertEqual(str(scholarship), expected)


class ScholarshipServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )
        self.discount = Discount.objects.create(
            name="Athletic Grant",
            discount_type=DiscountType.FIXED,
            value=Decimal('15000.00'),
            is_percentage=False
        )
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="test")

    def test_create_scholarship(self):
        scholarship = ScholarshipService.create_scholarship(
            student=self.student,
            discount=self.discount,
            scholarship_type=ScholarshipType.ATHLETIC,
            awarded_date=date(2025, 6, 1),
            expiry_date=date(2026, 5, 31),
            is_renewable=True,
            grantor="Sports Department",
            approved_by=self.user
        )
        self.assertEqual(scholarship.student, self.student)
        self.assertEqual(scholarship.scholarship_type, ScholarshipType.ATHLETIC)

    def test_get_scholarships_by_student(self):
        Scholarship.objects.create(student=self.student, discount=self.discount, scholarship_type=ScholarshipType.GOVERNMENT, awarded_date=date(2025,6,1))
        scholarships = ScholarshipService.get_scholarships_by_student(self.student.id)
        self.assertEqual(scholarships.count(), 1)

    def test_renew_scholarship(self):
        scholarship = Scholarship.objects.create(
            student=self.student, discount=self.discount, scholarship_type=ScholarshipType.PRIVATE,
            awarded_date=date(2025,6,1), expiry_date=date(2026,5,31)
        )
        renewed = ScholarshipService.renew_scholarship(scholarship, date(2027,5,31))
        self.assertEqual(renewed.expiry_date, date(2027,5,31))


class ScholarshipSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )
        self.discount = Discount.objects.create(
            name="Need-Based",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal('50.00'),
            is_percentage=True
        )
        self.user = User.objects.create_user(username="registrar", email="reg@example.com", password="test")

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "discount_id": self.discount.id,
            "scholarship_type": ScholarshipType.NEED_BASED,
            "awarded_date": "2025-06-01",
            "expiry_date": "2026-05-31",
            "is_renewable": False,
            "grantor": "Government",
            "approved_by_id": self.user.id
        }
        serializer = ScholarshipCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        scholarship = serializer.save()
        self.assertEqual(scholarship.student, self.student)

    def test_update_serializer(self):
        scholarship = Scholarship.objects.create(
            student=self.student, discount=self.discount, scholarship_type=ScholarshipType.GOVERNMENT,
            awarded_date=date(2025,6,1), expiry_date=date(2026,5,31)
        )
        data = {"expiry_date": "2027-05-31", "terms": "Renewable if GPA >= 2.5"}
        serializer = ScholarshipUpdateSerializer(scholarship, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.expiry_date, date(2027,5,31))

    def test_display_serializer(self):
        scholarship = Scholarship.objects.create(
            student=self.student, discount=self.discount, scholarship_type=ScholarshipType.NEED_BASED,
            awarded_date=date(2025,6,1)
        )
        serializer = ScholarshipDisplaySerializer(scholarship)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)
        self.assertEqual(serializer.data["discount"]["id"], self.discount.id)