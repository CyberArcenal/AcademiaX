from django.test import TestCase
from decimal import Decimal
from datetime import date
from users.models import User
from hr.models import Department, Position, Employee, PayrollPeriod, Payslip
from hr.services.payslip import PayslipService
from hr.serializers.payslip import (
    PayslipCreateSerializer,
    PayslipUpdateSerializer,
    PayslipDisplaySerializer,
)


class PayslipModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp1", email="emp1@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-001", hire_date=date(2025,1,1))
        self.period = PayrollPeriod.objects.create(
            name="January 1-15, 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 15)
        )

    def test_create_payslip(self):
        payslip = Payslip.objects.create(
            employee=self.employee,
            period=self.period,
            basic_pay=Decimal('15000.00'),
            overtime_pay=Decimal('1000.00'),
            allowances=Decimal('500.00'),
            bonuses=Decimal('0.00'),
            gross_pay=Decimal('16500.00'),
            sss_contribution=Decimal('500.00'),
            pagibig_contribution=Decimal('100.00'),
            philhealth_contribution=Decimal('200.00'),
            withholding_tax=Decimal('1500.00'),
            other_deductions=Decimal('0.00'),
            total_deductions=Decimal('2300.00'),
            net_pay=Decimal('14200.00')
        )
        self.assertEqual(payslip.employee, self.employee)
        self.assertEqual(payslip.net_pay, Decimal('14200.00'))

    def test_str_method(self):
        payslip = Payslip.objects.create(employee=self.employee, period=self.period)
        expected = f"Payslip for {self.employee} - {self.period.name}"
        self.assertEqual(str(payslip), expected)


class PayslipServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp2", email="emp2@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-002", hire_date=date(2025,1,1))
        self.period = PayrollPeriod.objects.create(
            name="February 1-15, 2025",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 15)
        )

    def test_generate_payslip(self):
        payslip = PayslipService.generate_payslip(
            employee=self.employee,
            period=self.period,
            basic_pay=Decimal('20000.00'),
            overtime_pay=Decimal('2000.00'),
            allowances=Decimal('1000.00'),
            sss_contribution=Decimal('600.00'),
            pagibig_contribution=Decimal('100.00'),
            philhealth_contribution=Decimal('250.00'),
            withholding_tax=Decimal('2000.00')
        )
        self.assertEqual(payslip.employee, self.employee)
        self.assertEqual(payslip.gross_pay, Decimal('23000.00'))  # 20000+2000+1000
        self.assertEqual(payslip.total_deductions, Decimal('2950.00'))  # 600+100+250+2000
        self.assertEqual(payslip.net_pay, Decimal('20050.00'))

    def test_get_payslips_by_employee(self):
        Payslip.objects.create(employee=self.employee, period=self.period, basic_pay=10000, gross_pay=10000, net_pay=8000)
        payslips = PayslipService.get_payslips_by_employee(self.employee.id)
        self.assertEqual(payslips.count(), 1)

    def test_mark_paid(self):
        payslip = Payslip.objects.create(employee=self.employee, period=self.period, basic_pay=10000, gross_pay=10000, net_pay=8000)
        marked = PayslipService.mark_paid(payslip, date(2025, 2, 20))
        self.assertEqual(marked.payment_date, date(2025, 2, 20))

    def test_update_payslip(self):
        payslip = Payslip.objects.create(employee=self.employee, period=self.period, basic_pay=10000, gross_pay=10000, net_pay=8000)
        updated = PayslipService.update_payslip(payslip, {"basic_pay": 12000, "allowances": 500})
        self.assertEqual(updated.basic_pay, 12000)
        self.assertEqual(updated.allowances, 500)
        # Recalculation should happen automatically
        self.assertEqual(updated.gross_pay, 12500)  # 12000+0+500


class PayslipSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="emp3", email="emp3@example.com", password="test")
        self.employee = Employee.objects.create(user=self.user, employee_number="EMP-003", hire_date=date(2025,1,1))
        self.period = PayrollPeriod.objects.create(
            name="March 1-15, 2025",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 15)
        )

    def test_create_serializer_valid(self):
        data = {
            "employee_id": self.employee.id,
            "period_id": self.period.id,
            "basic_pay": "18000.00",
            "overtime_pay": "500.00",
            "allowances": "200.00",
            "sss_contribution": "500.00",
            "pagibig_contribution": "100.00",
            "philhealth_contribution": "200.00",
            "withholding_tax": "1500.00"
        }
        serializer = PayslipCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        payslip = serializer.save()
        self.assertEqual(payslip.employee, self.employee)

    def test_update_serializer(self):
        payslip = Payslip.objects.create(employee=self.employee, period=self.period, basic_pay=10000, gross_pay=10000, net_pay=8000)
        data = {"basic_pay": "11000", "allowances": "300"}
        serializer = PayslipUpdateSerializer(payslip, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.basic_pay, 11000)

    def test_display_serializer(self):
        payslip = Payslip.objects.create(employee=self.employee, period=self.period, basic_pay=12000, gross_pay=12000, net_pay=9500)
        serializer = PayslipDisplaySerializer(payslip)
        self.assertEqual(serializer.data["basic_pay"], "12000.00")
        self.assertEqual(serializer.data["net_pay"], "9500.00")
        self.assertEqual(serializer.data["employee"]["id"], self.employee.id)