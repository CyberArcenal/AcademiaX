from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date

from ..models.collection import CollectionReport
from ..models.payment import Payment
from ...users.models import User

class CollectionReportService:
    """Service for CollectionReport model operations"""

    @staticmethod
    def generate_daily_report(report_date: date, generated_by: Optional[User] = None) -> CollectionReport:
        try:
            with transaction.atomic():
                # Calculate totals
                payments = Payment.objects.filter(payment_date=report_date, is_verified=True)
                total_collections = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
                total_assessments = Decimal('0')  # Would need assessment data
                total_outstanding = Decimal('0')  # Would need assessment data

                # Payment method breakdown
                method_breakdown = {}
                for method in ['CASH', 'CHECK', 'BANK_TRANSFER', 'ONLINE', 'CARD']:
                    total = payments.filter(payment_method=method).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                    if total > 0:
                        method_breakdown[method] = float(total)

                report = CollectionReport(
                    report_date=report_date,
                    total_collections=total_collections,
                    total_assessments=total_assessments,
                    total_outstanding=total_outstanding,
                    payment_method_breakdown=method_breakdown,
                    generated_by=generated_by
                )
                report.full_clean()
                report.save()
                return report
        except ValidationError as e:
            raise

    @staticmethod
    def get_report_by_id(report_id: int) -> Optional[CollectionReport]:
        try:
            return CollectionReport.objects.get(id=report_id)
        except CollectionReport.DoesNotExist:
            return None

    @staticmethod
    def get_report_by_date(report_date: date) -> Optional[CollectionReport]:
        try:
            return CollectionReport.objects.get(report_date=report_date)
        except CollectionReport.DoesNotExist:
            return None

    @staticmethod
    def get_reports(date_range_start: Optional[date] = None, date_range_end: Optional[date] = None) -> List[CollectionReport]:
        queryset = CollectionReport.objects.all()
        if date_range_start:
            queryset = queryset.filter(report_date__gte=date_range_start)
        if date_range_end:
            queryset = queryset.filter(report_date__lte=date_range_end)
        return queryset.order_by('-report_date')

    @staticmethod
    def delete_report(report: CollectionReport) -> bool:
        try:
            report.delete()
            return True
        except Exception:
            return False