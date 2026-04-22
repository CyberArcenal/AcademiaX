from rest_framework import serializers
from teachers.models import TeacherQualification
from teachers.models.teacher import Teacher
from .teacher import TeacherMinimalSerializer


class TeacherQualificationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for teacher qualifications."""

    teacher = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = TeacherQualification
        fields = ["id", "teacher", "qualification_name", "date_earned", "expiry_date"]
        read_only_fields = fields


class TeacherQualificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a teacher qualification."""

    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )

    class Meta:
        model = TeacherQualification
        fields = "__all__"

    def create(self, validated_data) -> TeacherQualification:
        from teachers.services.teacher_qualification import TeacherQualificationService

        return TeacherQualificationService.create_qualification(**validated_data)


class TeacherQualificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a teacher qualification."""

    class Meta:
        model = TeacherQualification
        fields = ["qualification_name", "issuing_body", "expiry_date", "attachment_url"]

    def update(self, instance, validated_data) -> TeacherQualification:
        from teachers.services.teacher_qualification import TeacherQualificationService

        return TeacherQualificationService.update_qualification(instance, validated_data)


class TeacherQualificationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a teacher qualification."""

    teacher = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = TeacherQualification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]