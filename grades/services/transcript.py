from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date

from ..models.transcript import Transcript
from students.models.student import Student

class TranscriptService:
    """Service for Transcript model operations"""

    @staticmethod
    def create_transcript(
        student: Student,
        cumulative_gwa: Optional[Decimal] = None,
        total_units_completed: Decimal = Decimal('0'),
        graduation_date: Optional[date] = None,
        is_official: bool = False,
        notes: str = ""
    ) -> Transcript:
        try:
            with transaction.atomic():
                existing = Transcript.objects.filter(student=student).first()
                if existing:
                    raise ValidationError("Transcript already exists for this student")

                transcript = Transcript(
                    student=student,
                    cumulative_gwa=cumulative_gwa,
                    total_units_completed=total_units_completed,
                    graduation_date=graduation_date,
                    is_official=is_official,
                    notes=notes
                )
                transcript.full_clean()
                transcript.save()
                return transcript
        except ValidationError as e:
            raise

    @staticmethod
    def get_transcript_by_id(transcript_id: int) -> Optional[Transcript]:
        try:
            return Transcript.objects.get(id=transcript_id)
        except Transcript.DoesNotExist:
            return None

    @staticmethod
    def get_transcript_by_student(student_id: int) -> Optional[Transcript]:
        try:
            return Transcript.objects.get(student_id=student_id)
        except Transcript.DoesNotExist:
            return None

    @staticmethod
    def update_transcript(transcript: Transcript, update_data: Dict[str, Any]) -> Transcript:
        try:
            with transaction.atomic():
                for field, value in update_data.items():
                    if hasattr(transcript, field):
                        setattr(transcript, field, value)
                transcript.full_clean()
                transcript.save()
                return transcript
        except ValidationError as e:
            raise

    @staticmethod
    def compute_cumulative_gwa(student_id: int) -> Decimal:
        """Compute cumulative GWA from all final grades"""
        from .final_grade import FinalGrade
        finals = FinalGrade.objects.filter(student_id=student_id, status='APP')
        if not finals:
            return Decimal('0')
        total = sum((f.final_grade or 0) for f in finals)
        return total / len(finals)

    @staticmethod
    def mark_official(transcript: Transcript) -> Transcript:
        transcript.is_official = True
        transcript.save()
        return transcript

    @staticmethod
    def delete_transcript(transcript: Transcript) -> bool:
        try:
            transcript.delete()
            return True
        except Exception:
            return False