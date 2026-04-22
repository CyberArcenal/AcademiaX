from django.test import TestCase
from datetime import date
from students.models import Student
from alumni.models import Alumni, Employment
from alumni.services.employment import EmploymentService
from alumni.serializers.employment import (
    EmploymentCreateSerializer,
    EmploymentUpdateSerializer,
    EmploymentDisplaySerializer,
)
from common.enums.alumni import EmploymentType


class EmploymentModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2000-01-01",
            gender="M"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )

    def test_create_employment(self):
        emp = Employment.objects.create(
            alumni=self.alumni,
            job_title="Software Engineer",
            company_name="Tech Corp",
            employment_type=EmploymentType.FULL_TIME,
            start_date=date(2025, 6, 1),
            is_current=True
        )
        self.assertEqual(emp.alumni, self.alumni)
        self.assertEqual(emp.job_title, "Software Engineer")
        self.assertTrue(emp.is_current)

    def test_only_one_current_employment(self):
        Employment.objects.create(
            alumni=self.alumni,
            job_title="Engineer",
            company_name="Company A",
            start_date=date(2025, 1, 1),
            is_current=True
        )
        Employment.objects.create(
            alumni=self.alumni,
            job_title="Senior Engineer",
            company_name="Company B",
            start_date=date(2025, 6, 1),
            is_current=True
        )
        current_count = Employment.objects.filter(alumni=self.alumni, is_current=True).count()
        # The service should handle this, but model itself allows multiple; we test service logic separately.
        # For model test, just check creation.
        self.assertEqual(current_count, 2)  # Model allows, service enforces single current

    def test_str_method(self):
        emp = Employment.objects.create(
            alumni=self.alumni,
            job_title="Developer",
            company_name="Dev Inc",
            start_date=date(2025, 1, 1)
        )
        expected = f"{self.alumni} - Developer at Dev Inc"
        self.assertEqual(str(emp), expected)


class EmploymentServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria",
            last_name="Santos",
            birth_date="2001-02-02",
            gender="F"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )

    def test_create_employment(self):
        emp = EmploymentService.create_employment(
            alumni=self.alumni,
            job_title="Data Analyst",
            company_name="Data Corp",
            start_date=date(2025, 1, 1),
            is_current=True
        )
        self.assertEqual(emp.alumni, self.alumni)
        self.assertEqual(emp.job_title, "Data Analyst")
        self.assertTrue(emp.is_current)

    def test_set_current_unset_previous(self):
        emp1 = EmploymentService.create_employment(
            alumni=self.alumni,
            job_title="Junior",
            company_name="Company A",
            start_date=date(2024, 1, 1),
            is_current=True
        )
        emp2 = EmploymentService.create_employment(
            alumni=self.alumni,
            job_title="Senior",
            company_name="Company B",
            start_date=date(2025, 1, 1),
            is_current=True
        )
        emp1.refresh_from_db()
        self.assertFalse(emp1.is_current)
        self.assertTrue(emp2.is_current)

    def test_get_current_employment(self):
        Employment.objects.create(
            alumni=self.alumni,
            job_title="Old Job",
            company_name="Old Co",
            start_date=date(2024, 1, 1),
            is_current=False
        )
        current = Employment.objects.create(
            alumni=self.alumni,
            job_title="Current Job",
            company_name="Current Co",
            start_date=date(2025, 1, 1),
            is_current=True
        )
        fetched = EmploymentService.get_current_employment(self.alumni.id)
        self.assertEqual(fetched, current)

    def test_update_employment(self):
        emp = Employment.objects.create(
            alumni=self.alumni,
            job_title="Tester",
            company_name="Test Inc",
            start_date=date(2025, 1, 1),
            is_current=False
        )
        updated = EmploymentService.update_employment(
            emp,
            {"job_title": "Senior Tester", "is_current": True}
        )
        self.assertEqual(updated.job_title, "Senior Tester")
        self.assertTrue(updated.is_current)


class EmploymentSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro",
            last_name="Penduko",
            birth_date="2002-03-03",
            gender="M"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )

    def test_create_serializer_valid(self):
        data = {
            "alumni_id": self.alumni.id,
            "job_title": "Manager",
            "company_name": "Biz Corp",
            "start_date": "2025-01-01",
            "employment_type": EmploymentType.FULL_TIME,
            "is_current": True
        }
        serializer = EmploymentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        emp = serializer.save()
        self.assertEqual(emp.alumni, self.alumni)

    def test_update_serializer(self):
        emp = Employment.objects.create(
            alumni=self.alumni,
            job_title="Analyst",
            company_name="Analytics Inc",
            start_date=date(2025, 1, 1)
        )
        data = {"job_title": "Lead Analyst", "is_current": True}
        serializer = EmploymentUpdateSerializer(emp, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.job_title, "Lead Analyst")

    def test_display_serializer(self):
        emp = Employment.objects.create(
            alumni=self.alumni,
            job_title="Consultant",
            company_name="Consulting Group",
            start_date=date(2025, 1, 1)
        )
        serializer = EmploymentDisplaySerializer(emp)
        self.assertEqual(serializer.data["job_title"], "Consultant")
        self.assertEqual(serializer.data["alumni"]["id"], self.alumni.id)