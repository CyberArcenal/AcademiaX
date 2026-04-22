from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any

from ..models.medical_record import MedicalRecord
from ..models.student import Student
from common.enums.students import BloodType

class MedicalRecordService:
    """Service for MedicalRecord model operations"""

    @staticmethod
    def create_or_update_record(
        student: Student,
        blood_type: str = BloodType.UNKNOWN,
        allergies: str = "",
        medical_conditions: str = "",
        medications: str = "",
        emergency_contact_name: str = "",
        emergency_contact_number: str = "",
        health_insurance_provider: str = "",
        health_insurance_number: str = "",
        physician_name: str = "",
        physician_contact: str = "",
        notes: str = ""
    ) -> MedicalRecord:
        try:
            with transaction.atomic():
                record, created = MedicalRecord.objects.update_or_create(
                    student=student,
                    defaults={
                        'blood_type': blood_type,
                        'allergies': allergies,
                        'medical_conditions': medical_conditions,
                        'medications': medications,
                        'emergency_contact_name': emergency_contact_name,
                        'emergency_contact_number': emergency_contact_number,
                        'health_insurance_provider': health_insurance_provider,
                        'health_insurance_number': health_insurance_number,
                        'physician_name': physician_name,
                        'physician_contact': physician_contact,
                        'notes': notes
                    }
                )
                record.full_clean()
                record.save()
                return record
        except ValidationError as e:
            raise

    @staticmethod
    def get_medical_record_by_student(student_id: int) -> Optional[MedicalRecord]:
        try:
            return MedicalRecord.objects.get(student_id=student_id)
        except MedicalRecord.DoesNotExist:
            return None

    @staticmethod
    def delete_medical_record(record: MedicalRecord) -> bool:
        try:
            record.delete()
            return True
        except Exception:
            return False