from rest_framework import serializers
from academic.models import Subject
from attendance.models import StudentAttendance
from classes.models.academic_year import AcademicYear
from classes.models.section import Section
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer
from classes.serializers.section import SectionMinimalSerializer
from academic.serializers.subject import SubjectMinimalSerializer
from classes.serializers.academic_year import AcademicYearMinimalSerializer
from teachers.models.teacher import Teacher
from teachers.serializers.teacher import TeacherMinimalSerializer


class StudentAttendanceMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for student attendance."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = StudentAttendance
        fields = ["id", "student", "date", "status", "time_in"]
        read_only_fields = fields


class StudentAttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a student attendance record."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    marked_by_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="marked_by", required=False, allow_null=True
    )

    class Meta:
        model = StudentAttendance
        fields = "__all__"

    def create(self, validated_data) -> StudentAttendance:
        from attendance.services.student_attendance import StudentAttendanceService

        return StudentAttendanceService.create_attendance(**validated_data)


class StudentAttendanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a student attendance record."""

    class Meta:
        model = StudentAttendance
        fields = ["status", "time_in", "time_out", "late_minutes", "late_reason", "remarks"]

    def update(self, instance, validated_data) -> StudentAttendance:
        from attendance.services.student_attendance import StudentAttendanceService

        return StudentAttendanceService.update_attendance(instance, validated_data)


class StudentAttendanceDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a student attendance record."""

    student = StudentMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    marked_by = TeacherMinimalSerializer(read_only=True)

    class Meta:
        model = StudentAttendance
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]