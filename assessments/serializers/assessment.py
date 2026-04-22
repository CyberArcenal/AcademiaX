from rest_framework import serializers
from academic.models.subject import Subject
from assessments.models import Assessment
from academic.serializers.subject import SubjectMinimalSerializer
from teachers.models.teacher import Teacher
from teachers.serializers.teacher import TeacherMinimalSerializer


class AssessmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for assessments."""

    subject = SubjectMinimalSerializer(read_only=True)
    teacher = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = Assessment
        fields = ["id", "title", "subject", "teacher", "assessment_type", "due_date", "total_points"]
        read_only_fields = fields


class AssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an assessment."""

    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )

    class Meta:
        model = Assessment
        fields = "__all__"

    def create(self, validated_data) -> Assessment:
        from assessments.services.assessment import AssessmentService

        return AssessmentService.create_assessment(**validated_data)


class AssessmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an assessment."""

    class Meta:
        model = Assessment
        fields = [
            "title", "description", "total_points", "passing_points",
            "duration_minutes", "due_date", "open_date", "close_date",
            "allow_late_submission", "late_deduction_per_day",
            "attempts_allowed", "show_answers_after_submission"
        ]

    def update(self, instance, validated_data) -> Assessment:
        from assessments.services.assessment import AssessmentService

        return AssessmentService.update_assessment(instance, validated_data)


class AssessmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an assessment."""

    subject = SubjectMinimalSerializer(read_only=True)
    teacher = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = Assessment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]