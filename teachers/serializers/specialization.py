from rest_framework import serializers
from academic.models.subject import Subject
from teachers.models import Specialization
from teachers.models.teacher import Teacher
from .teacher import TeacherMinimalSerializer
from academic.serializers.subject import SubjectMinimalSerializer


class SpecializationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for specializations."""

    teacher = TeacherMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = Specialization
        fields = ["id", "teacher", "subject", "is_primary", "proficiency_level"]
        read_only_fields = fields


class SpecializationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a specialization."""

    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )

    class Meta:
        model = Specialization
        fields = ["teacher_id", "subject_id", "is_primary", "proficiency_level"]

    def create(self, validated_data) -> Specialization:
        from teachers.services.specialization import SpecializationService

        return SpecializationService.create_specialization(**validated_data)


class SpecializationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a specialization."""

    class Meta:
        model = Specialization
        fields = ["is_primary", "proficiency_level"]

    def update(self, instance, validated_data) -> Specialization:
        from teachers.services.specialization import SpecializationService

        return SpecializationService.update_specialization(instance, validated_data)


class SpecializationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a specialization."""

    teacher = TeacherMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = Specialization
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]