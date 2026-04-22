from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from hr.models import SalaryGrade, PayrollPeriod
from hr.services.payroll import SalaryGradeService, PayrollPeriodService
from hr.serializers.payroll import (
    SalaryGradeCreateSerializer,
    SalaryGradeUpdateSerializer,
    SalaryGradeDisplaySerializer,
    PayrollPeriodCreateSerializer,
    PayrollPeriodUpdateSerializer,
    PayrollPeriodDisplaySerializer,
)


class SalaryGradeModelTest(TestCase):
    def test_create_salary_grade(self):
        sg = SalaryGrade.objects.create(
            grade=1,
            basic_salary=Decimal('20000.00'),
            hourly_rate=Decimal('120.00'),
            description="Entry level"
        )
        self.assertEqual(sg.grade, 1)
        self.assertEqual(sg.basic_salary, Decimal('20000.00'))

    def test_str_method(self):
        sg = SalaryGrade.objects.create(grade=5, basic_salary=Decimal('50000.00'))
        self.assertEqual(str(sg), f"Grade 5 - 50000.00")


class SalaryGradeServiceTest(TestCase):
    def test_create_salary_grade(self):
        sg = SalaryGradeService.create_salary_grade(
            grade=2,
            basic_salary=Decimal('25000.00'),
            hourly_rate=Decimal('150.00')
        )
        self.assertEqual(sg.grade, 2)

    def test_get_salary_grade_by_level(self):
        created = SalaryGrade.objects.create(grade=3, basic_salary=Decimal('30000.00'))
        fetched = SalaryGradeService.get_salary_grade_by_level(3)
        self.assertEqual(fetched, created)

    def test_update_salary_grade(self):
        sg = SalaryGrade.objects.create(grade=4, basic_salary=Decimal('40000.00'))
        updated = SalaryGradeService.update_salary_grade(sg, {"basic_salary": Decimal('45000.00'), "description": "Senior"})
        self.assertEqual(updated.basic_salary, Decimal('45000.00'))


class SalaryGradeSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "grade": 6,
            "basic_salary": "60000.00",
            "hourly_rate": "350.00",
            "description": "Manager"
        }
        serializer = SalaryGradeCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        sg = serializer.save()
        self.assertEqual(sg.grade, 6)

    def test_update_serializer(self):
        sg = SalaryGrade.objects.create(grade=7, basic_salary=Decimal('70000.00'))
        data = {"basic_salary": "75000.00"}
        serializer = SalaryGradeUpdateSerializer(sg, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.basic_salary, Decimal('75000.00'))

    def test_display_serializer(self):
        sg = SalaryGrade.objects.create(grade=8, basic_salary=Decimal('80000.00'))
        serializer = SalaryGradeDisplaySerializer(sg)
        self.assertEqual(serializer.data["grade"], 8)


class PayrollPeriodModelTest(TestCase):
    def test_create_payroll_period(self):
        period = PayrollPeriod.objects.create(
            name="January 1-15, 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 15),
            is_closed=False
        )
        self.assertEqual(period.name, "January 1-15, 2025")
        self.assertFalse(period.is_closed)

    def test_str_method(self):
        period = PayrollPeriod.objects.create(name="Test Period", start_date=date(2025,2,1), end_date=date(2025,2,15))
        self.assertEqual(str(period), "Test Period")


class PayrollPeriodServiceTest(TestCase):
    def test_create_payroll_period(self):
        period = PayrollPeriodService.create_payroll_period(
            name="February 1-15, 2025",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 15)
        )
        self.assertEqual(period.name, "February 1-15, 2025")

    def test_get_current_payroll_period(self):
        today = date.today()
        current = PayrollPeriod.objects.create(
            name="Current Period",
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=5),
            is_closed=False
        )
        fetched = PayrollPeriodService.get_current_payroll_period()
        self.assertEqual(fetched, current)

    def test_close_period(self):
        period = PayrollPeriod.objects.create(name="To Close", start_date=date(2025,3,1), end_date=date(2025,3,15), is_closed=False)
        closed = PayrollPeriodService.close_period(period)
        self.assertTrue(closed.is_closed)
        self.assertIsNotNone(closed.closed_at)


class PayrollPeriodSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "name": "March 1-15, 2025",
            "start_date": "2025-03-01",
            "end_date": "2025-03-15"
        }
        serializer = PayrollPeriodCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        period = serializer.save()
        self.assertEqual(period.name, "March 1-15, 2025")

    def test_update_serializer(self):
        period = PayrollPeriod.objects.create(name="Old", start_date=date(2025,4,1), end_date=date(2025,4,15))
        data = {"name": "Updated Period", "is_closed": True}
        serializer = PayrollPeriodUpdateSerializer(period, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated Period")

    def test_display_serializer(self):
        period = PayrollPeriod.objects.create(name="Display", start_date=date(2025,5,1), end_date=date(2025,5,15))
        serializer = PayrollPeriodDisplaySerializer(period)
        self.assertEqual(serializer.data["name"], "Display")