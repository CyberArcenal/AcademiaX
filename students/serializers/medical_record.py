from rest_framework import serializers
from students.models import MedicalRecord
from students.models.student import Student
from .student import StudentMinimalSerializer


class MedicalRecordMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for medical records."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = MedicalRecord
        fields = ["id", "student", "blood_type", "allergies"]
        read_only_fields = fields


class MedicalRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating or updating a medical record."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )

    class Meta:
        model = MedicalRecord
        fields = "__all__"

    def create(self, validated_data) -> MedicalRecord:
        from students.services.medical_record import MedicalRecordService

        return MedicalRecordService.create_or_update_record(**validated_data)


class MedicalRecordUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a medical record."""

    class Meta:
        model = MedicalRecord
        fields = [
            "blood_type", "allergies", "medical_conditions", "medications",
            "emergency_contact_name", "emergency_contact_number",
            "health_insurance_provider", "health_insurance_number",
            "physician_name", "physician_contact", "notes"
        ]

    def update(self, instance, validated_data) -> MedicalRecord:
        from students.services.medical_record import MedicalRecordService

        return MedicalRecordService.create_or_update_record(
            student=instance.student, **validated_data
        )


class MedicalRecordDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a medical record."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = MedicalRecord
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]