from rest_framework import serializers
from assessments.models import AssessmentGrade
from .submission import SubmissionMinimalSerializer


class AssessmentGradeMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for assessment grades."""

    submission = SubmissionMinimalSerializer(read_only=True)

    class Meta:
        model = AssessmentGrade
        fields = ["id", "submission", "raw_score", "percentage_score", "transmuted_grade"]
        read_only_fields = fields


class AssessmentGradeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an assessment grade."""

    submission_id = serializers.PrimaryKeyRelatedField(
        queryset=Submission.objects.all(), source="submission"
    )

    class Meta:
        model = AssessmentGrade
        fields = ["submission_id", "raw_score", "percentage_score", "transmuted_grade", "remarks"]

    def create(self, validated_data) -> AssessmentGrade:
        from assessments.services.grade import AssessmentGradeService

        return AssessmentGradeService.create_or_update_grade(**validated_data)


class AssessmentGradeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an assessment grade."""

    class Meta:
        model = AssessmentGrade
        fields = ["raw_score", "percentage_score", "transmuted_grade", "remarks"]

    def update(self, instance, validated_data) -> AssessmentGrade:
        from assessments.services.grade import AssessmentGradeService

        return AssessmentGradeService.create_or_update_grade(
            submission=instance.submission, **validated_data
        )


class AssessmentGradeDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an assessment grade."""

    submission = SubmissionMinimalSerializer(read_only=True)

    class Meta:
        model = AssessmentGrade
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]