from rest_framework import serializers
from assessments.models import Submission
from students.serializers.student import StudentMinimalSerializer
from .assessment import AssessmentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class SubmissionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for submissions."""

    assessment = AssessmentMinimalSerializer(read_only=True)
    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = ["id", "assessment", "student", "status", "submitted_at", "score"]
        read_only_fields = fields


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a submission."""

    assessment_id = serializers.PrimaryKeyRelatedField(
        queryset=Assessment.objects.all(), source="assessment"
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )

    class Meta:
        model = Submission
        fields = ["assessment_id", "student_id", "ip_address"]

    def create(self, validated_data) -> Submission:
        from assessments.services.submission import SubmissionService

        return SubmissionService.create_submission(**validated_data)


class SubmissionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a submission (e.g., grading)."""

    graded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="graded_by", required=False, allow_null=True
    )

    class Meta:
        model = Submission
        fields = ["score", "feedback", "graded_by_id", "status"]

    def update(self, instance, validated_data) -> Submission:
        from assessments.services.submission import SubmissionService

        return SubmissionService.update_submission(instance, validated_data)


class SubmissionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a submission."""

    assessment = AssessmentMinimalSerializer(read_only=True)
    student = StudentMinimalSerializer(read_only=True)
    graded_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "submitted_at"]