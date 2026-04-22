from rest_framework import serializers
from assessments.models import Choice
from assessments.models.question import Question
from .question import QuestionMinimalSerializer


class ChoiceMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for choices."""

    question = QuestionMinimalSerializer(read_only=True)

    class Meta:
        model = Choice
        fields = ["id", "question", "choice_text", "order"]
        read_only_fields = fields


class ChoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a choice."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(), source="question"
    )

    class Meta:
        model = Choice
        fields = "__all__"

    def create(self, validated_data) -> Choice:
        from assessments.services.choice import ChoiceService

        return ChoiceService.create_choice(**validated_data)


class ChoiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a choice."""

    class Meta:
        model = Choice
        fields = ["choice_text", "is_correct", "order"]

    def update(self, instance, validated_data) -> Choice:
        from assessments.services.choice import ChoiceService

        return ChoiceService.update_choice(instance, validated_data)


class ChoiceDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a choice."""

    question = QuestionMinimalSerializer(read_only=True)

    class Meta:
        model = Choice
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]