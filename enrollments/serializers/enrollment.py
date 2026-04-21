from rest_framework import serializers
from enrollments.models import Enrollment
from students.serializers.student import StudentMinimalSerializer
from classes.serializers.academic_year import AcademicYearMinimalSerializer
from classes.serializers.grade_level import GradeLevelMinimalSerializer
from classes.serializers.section import SectionMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class EnrollmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for enrollments."""

    student = StudentMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    grade_level = GradeLevelMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "academic_year", "grade_level", "section", "status", "enrollment_date"]
        read_only_fields = fields


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an enrollment."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    grade_level_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeLevel.objects.all(), source="grade_level"
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section"
    )
    processed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="processed_by", required=False, allow_null=True
    )

    class Meta:
        model = Enrollment
        fields = [
            "student_id", "academic_year_id", "grade_level_id", "section_id",
            "processed_by_id", "previous_school", "lrn", "remarks"
        ]

    def create(self, validated_data) -> Enrollment:
        from enrollments.services.enrollment import EnrollmentService

        return EnrollmentService.create_enrollment(**validated_data)


class EnrollmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an enrollment (status, section transfer)."""

    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section", required=False
    )

    class Meta:
        model = Enrollment
        fields = ["status", "section_id", "payment_status", "remarks"]

    def update(self, instance, validated_data) -> Enrollment:
        from enrollments.services.enrollment import EnrollmentService

        if 'section_id' in validated_data and validated_data['section_id'] != instance.section:
            return EnrollmentService.transfer_section(instance, validated_data.pop('section_id'))
        return EnrollmentService.update_enrollment(instance, validated_data)


class EnrollmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an enrollment."""

    student = StudentMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    grade_level = GradeLevelMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)
    processed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "enrollment_date"]