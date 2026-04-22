from rest_framework import serializers
from academic.models.subject import Subject
from enrollments.models import SubjectEnrollment
from enrollments.models.enrollment import Enrollment
from teachers.models.teacher import Teacher
from .enrollment import EnrollmentMinimalSerializer
from academic.serializers.subject import SubjectMinimalSerializer
from teachers.serializers.teacher import TeacherMinimalSerializer


class SubjectEnrollmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for subject enrollments."""

    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = SubjectEnrollment
        fields = ["id", "subject", "is_dropped", "final_grade"]
        read_only_fields = fields


class SubjectEnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for enrolling a student in a subject."""

    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source="enrollment"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher", required=False, allow_null=True
    )

    class Meta:
        model = SubjectEnrollment
        fields = ["enrollment_id", "subject_id", "teacher_id"]

    def create(self, validated_data) -> SubjectEnrollment:
        from enrollments.services.subject_enrollment import SubjectEnrollmentService

        return SubjectEnrollmentService.enroll_subject(**validated_data)


class SubjectEnrollmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a subject enrollment (drop, grade)."""

    class Meta:
        model = SubjectEnrollment
        fields = ["is_dropped", "drop_reason", "final_grade"]

    def update(self, instance, validated_data) -> SubjectEnrollment:
        from enrollments.services.subject_enrollment import SubjectEnrollmentService

        if validated_data.get('is_dropped') and not instance.is_dropped:
            return SubjectEnrollmentService.drop_subject(instance, validated_data.get('drop_reason', ''))
        if 'final_grade' in validated_data:
            return SubjectEnrollmentService.update_final_grade(instance, validated_data['final_grade'])
        return instance


class SubjectEnrollmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a subject enrollment."""

    enrollment = EnrollmentMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    teacher = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = SubjectEnrollment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]