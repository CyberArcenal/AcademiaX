from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date

from ..models.payroll import Payslip
from ..models.employee import Employee
from ..models.payroll import PayrollPeriod

class PayslipService:
    """Service for Payslip model operations"""

    @staticmethod
    def generate_payslip(
        employee: Employee,
        period: PayrollPeriod,
        basic_pay: Decimal,
        overtime_pay: Decimal = Decimal('0'),
        allowances: Decimal = Decimal('0'),
        bonuses: Decimal = Decimal('0'),
        sss_contribution: Decimal = Decimal('0'),
        pagibig_contribution: Decimal = Decimal('0'),
        philhealth_contribution: Decimal = Decimal('0'),
        withholding_tax: Decimal = Decimal('0'),
        other_deductions: Decimal = Decimal('0'),
        bank_account: str = "",
        notes: str = ""
    ) -> Payslip:
        try:
            with transaction.atomic():
                gross_pay = basic_pay + overtime_pay + allowances + bonuses
                total_deductions = sss_contribution + pagibig_contribution + philhealth_contribution + withholding_tax + other_deductions
                net_pay = gross_pay - total_deductions

                payslip = Payslip(
                    employee=employee,
                    period=period,
                    basic_pay=basic_pay,
                    overtime_pay=overtime_pay,
                    allowances=allowances,
                    bonuses=bonuses,
                    gross_pay=gross_pay,
                    sss_contribution=sss_contribution,
                    pagibig_contribution=pagibig_contribution,
                    philhealth_contribution=philhealth_contribution,
                    withholding_tax=withholding_tax,
                    other_deductions=other_deductions,
                    total_deductions=total_deductions,
                    net_pay=net_pay,
                    bank_account=bank_account,
                    notes=notes
                )
                payslip.full_clean()
                payslip.save()
                return payslip
        except ValidationError as e:
            raise

    @staticmethod
    def get_payslip_by_id(payslip_id: int) -> Optional[Payslip]:
        try:
            return Payslip.objects.get(id=payslip_id)
        except Payslip.DoesNotExist:
            return None

    @staticmethod
    def get_payslips_by_employee(employee_id: int, limit: int = 12) -> List[Payslip]:
        return Payslip.objects.filter(employee_id=employee_id).order_by('-period__start_date')[:limit]

    @staticmethod
    def get_payslip_by_employee_period(employee_id: int, period_id: int) -> Optional[Payslip]:
        try:
            return Payslip.objects.get(employee_id=employee_id, period_id=period_id)
        except Payslip.DoesNotExist:
            return None

    @staticmethod
    def update_payslip(payslip: Payslip, update_data: Dict[str, Any]) -> Payslip:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(payslip, field):
                        setattr(payslip, field, value)
                # Recalculate totals if needed
                if any(f in update_data for f in ['basic_pay', 'overtime_pay', 'allowances', 'bonuses']):
                    payslip.gross_pay = payslip.basic_pay + payslip.overtime_pay + payslip.allowances + payslip.bonuses
                if any(f in update_data for f in ['sss_contribution', 'pagibig_contribution', 'philhealth_contribution', 'withholding_tax', 'other_deductions']):
                    payslip.total_deductions = payslip.sss_contribution + payslip.pagibig_contribution + payslip.philhealth_contribution + payslip.withholding_tax + payslip.other_deductions
                payslip.net_pay = payslip.gross_pay - payslip.total_deductions
                payslip.full_clean()
                payslip.save()
                return payslip
        except ValidationError as e:
            raise

    @staticmethod
    def mark_paid(payslip: Payslip, payment_date: date) -> Payslip:
        payslip.payment_date = payment_date
        payslip.save()
        return payslip

    @staticmethod
    def delete_payslip(payslip: Payslip) -> bool:
        try:
            payslip.delete()
            return True
        except Exception:
            return False