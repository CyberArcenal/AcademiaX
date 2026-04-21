from rest_framework import serializers
from attendance.models import StudentAttendanceSummary
from classes.models.academic_year import AcademicYear
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer
from classes.serializers.academic_year import AcademicYearMinimalSerializer


class StudentAttendanceSummaryMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for student attendance summaries."""

    student = StudentMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = StudentAttendanceSummary
        fields = ["id", "student", "academic_year", "term", "attendance_rate"]
        read_only_fields = fields


class StudentAttendanceSummaryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a student attendance summary."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )

    class Meta:
        model = StudentAttendanceSummary
        fields = "__all__"

    def create(self, validated_data) -> StudentAttendanceSummary:
        from attendance.services.attendance_summary import StudentAttendanceSummaryService

        return StudentAttendanceSummaryService.create_or_update_summary(**validated_data)


class StudentAttendanceSummaryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a student attendance summary."""

    class Meta:
        model = StudentAttendanceSummary
        fields = ["total_present", "total_absent", "total_late", "total_excused", "attendance_rate"]

    def update(self, instance, validated_data) -> StudentAttendanceSummary:
        from attendance.services.attendance_summary import StudentAttendanceSummaryService

        return StudentAttendanceSummaryService.create_or_update_summary(
            student=instance.student,
            academic_year=instance.academic_year,
            term=instance.term,
            **validated_data
        )


class StudentAttendanceSummaryDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a student attendance summary."""

    student = StudentMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = StudentAttendanceSummary
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]