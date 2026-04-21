from rest_framework import serializers
from academic.models import Prerequisite
from academic.models.subject import Subject
from .subject import SubjectMinimalSerializer


class PrerequisiteMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for prerequisites."""

    subject = SubjectMinimalSerializer(read_only=True)
    required_subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = Prerequisite
        fields = ["id", "subject", "required_subject", "is_optional"]
        read_only_fields = fields


class PrerequisiteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a prerequisite relationship."""

    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    required_subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="required_subject"
    )

    class Meta:
        model = Prerequisite
        fields = ["subject_id", "required_subject_id", "is_optional", "notes"]

    def create(self, validated_data) -> Prerequisite:
        from academic.services.prerequisite import PrerequisiteService

        return PrerequisiteService.add_prerequisite(**validated_data)


class PrerequisiteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a prerequisite relationship."""

    class Meta:
        model = Prerequisite
        fields = ["is_optional", "notes"]

    def update(self, instance, validated_data) -> Prerequisite:
        from academic.services.prerequisite import PrerequisiteService

        return PrerequisiteService.update_prerequisite(instance, **validated_data)


class PrerequisiteDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a prerequisite."""

    subject = SubjectMinimalSerializer(read_only=True)
    required_subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = Prerequisite
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]