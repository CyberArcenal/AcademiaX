from rest_framework import serializers
from academic.models import Subject


class SubjectMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for subjects."""

    class Meta:
        model = Subject
        fields = ["id", "code", "name", "units"]
        read_only_fields = fields


class SubjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a subject."""

    class Meta:
        model = Subject
        fields = ["code", "name", "description", "units", "subject_type"]

    def create(self, validated_data) -> Subject:
        from academic.services.subject import SubjectService

        return SubjectService.create_subject(**validated_data)


class SubjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a subject."""

    class Meta:
        model = Subject
        fields = ["name", "description", "units", "subject_type", "is_active"]

    def update(self, instance, validated_data) -> Subject:
        from academic.services.subject import SubjectService

        return SubjectService.update_subject(instance, validated_data)


class SubjectDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a subject."""

    class Meta:
        model = Subject
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]