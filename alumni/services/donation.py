from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from datetime import date
from django.db import models
from alumni.models.alumni import Alumni
from alumni.models.donation import Donation
from common.enums.alumni import DonationPurpose



class DonationService:
    """Service for Donation model operations"""

    @staticmethod
    def create_donation(
        alumni: Alumni,
        amount: float,
        date: date,
        purpose: str = DonationPurpose.GENERAL,
        receipt_number: str = "",
        is_anonymous: bool = False,
        remarks: str = ""
    ) -> Donation:
        try:
            with transaction.atomic():
                donation = Donation(
                    alumni=alumni,
                    amount=amount,
                    date=date,
                    purpose=purpose,
                    receipt_number=receipt_number,
                    is_anonymous=is_anonymous,
                    remarks=remarks
                )
                donation.full_clean()
                donation.save()
                return donation
        except ValidationError as e:
            raise

    @staticmethod
    def get_donation_by_id(donation_id: int) -> Optional[Donation]:
        try:
            return Donation.objects.get(id=donation_id)
        except Donation.DoesNotExist:
            return None

    @staticmethod
    def get_donations_by_alumni(alumni_id: int) -> List[Donation]:
        return Donation.objects.filter(alumni_id=alumni_id).order_by('-date')

    @staticmethod
    def update_donation(donation: Donation, update_data: Dict[str, Any]) -> Donation:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(donation, field):
                        setattr(donation, field, value)
                donation.full_clean()
                donation.save()
                return donation
        except ValidationError as e:
            raise

    @staticmethod
    def delete_donation(donation: Donation) -> bool:
        try:
            donation.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def get_total_donations_by_alumni(alumni_id: int) -> float:
        total = Donation.objects.filter(alumni_id=alumni_id).aggregate(total=models.Sum('amount'))['total']
        return total or 0.0

    @staticmethod
    def get_donations_by_purpose(purpose: str) -> List[Donation]:
        return Donation.objects.filter(purpose=purpose)