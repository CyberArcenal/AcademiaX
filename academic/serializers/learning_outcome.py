from rest_framework import serializers
from academic.models import LearningOutcome
from academic.models.subject import Subject
from .subject import SubjectMinimalSerializer


class LearningOutcomeMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for learning outcomes."""

    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = LearningOutcome
        fields = ["id", "subject", "code", "description"]
        read_only_fields = fields


class LearningOutcomeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a learning outcome."""

    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )

    class Meta:
        model = LearningOutcome
        fields = ["subject_id", "code", "description", "order"]

    def create(self, validated_data) -> LearningOutcome:
        from academic.services.learning_outcome import LearningOutcomeService

        return LearningOutcomeService.create_outcome(**validated_data)


class LearningOutcomeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a learning outcome."""

    class Meta:
        model = LearningOutcome
        fields = ["description", "order"]

    def update(self, instance, validated_data) -> LearningOutcome:
        from academic.services.learning_outcome import LearningOutcomeService

        return LearningOutcomeService.update_outcome(instance, validated_data)


class LearningOutcomeDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a learning outcome."""

    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = LearningOutcome
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]