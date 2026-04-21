from rest_framework import serializers
from assessments.models import Question
from .assessment import AssessmentMinimalSerializer


class QuestionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for questions."""

    assessment = AssessmentMinimalSerializer(read_only=True)

    class Meta:
        model = Question
        fields = ["id", "assessment", "question_text", "question_type", "points", "order"]
        read_only_fields = fields


class QuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a question."""

    assessment_id = serializers.PrimaryKeyRelatedField(
        queryset=Assessment.objects.all(), source="assessment"
    )

    class Meta:
        model = Question
        fields = "__all__"

    def create(self, validated_data) -> Question:
        from assessments.services.question import QuestionService

        return QuestionService.create_question(**validated_data)


class QuestionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a question."""

    class Meta:
        model = Question
        fields = ["question_text", "question_type", "points", "order", "explanation", "is_required"]

    def update(self, instance, validated_data) -> Question:
        from assessments.services.question import QuestionService

        return QuestionService.update_question(instance, validated_data)


class QuestionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a question."""

    assessment = AssessmentMinimalSerializer(read_only=True)

    class Meta:
        model = Question
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]