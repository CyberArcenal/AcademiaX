from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.students import BloodType
from .student import Student

class MedicalRecord(TimestampedModel, UUIDModel):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='medical_record')
    blood_type = models.CharField(max_length=3, choices=BloodType.choices, default=BloodType.UNKNOWN)
    allergies = models.TextField(blank=True, help_text="List of allergies")
    medical_conditions = models.TextField(blank=True, help_text="Asthma, diabetes, etc.")
    medications = models.TextField(blank=True, help_text="Regular medications")
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True)
    health_insurance_provider = models.CharField(max_length=100, blank=True)
    health_insurance_number = models.CharField(max_length=50, blank=True)
    physician_name = models.CharField(max_length=100, blank=True)
    physician_contact = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Medical Record - {self.student}"