from rest_framework import serializers
from assessments.models import Answer
from .submission import SubmissionMinimalSerializer
from .question import QuestionMinimalSerializer


class AnswerMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for answers."""

    submission = SubmissionMinimalSerializer(read_only=True)
    question = QuestionMinimalSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ["id", "submission", "question", "points_earned"]
        read_only_fields = fields


class AnswerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an answer."""

    submission_id = serializers.PrimaryKeyRelatedField(
        queryset=Submission.objects.all(), source="submission"
    )
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(), source="question"
    )
    selected_choice_id = serializers.PrimaryKeyRelatedField(
        queryset=Choice.objects.all(), source="selected_choice", required=False, allow_null=True
    )

    class Meta:
        model = Answer
        fields = ["submission_id", "question_id", "selected_choice_id", "text_answer", "matching_answer"]

    def create(self, validated_data) -> Answer:
        from assessments.services.answer import AnswerService

        return AnswerService.create_or_update_answer(**validated_data)


class AnswerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an answer (grading)."""

    class Meta:
        model = Answer
        fields = ["points_earned", "feedback"]

    def update(self, instance, validated_data) -> Answer:
        from assessments.services.answer import AnswerService

        return AnswerService.grade_answer(instance, **validated_data)


class AnswerDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an answer."""

    submission = SubmissionMinimalSerializer(read_only=True)
    question = QuestionMinimalSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]