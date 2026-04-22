from rest_framework import serializers
from academic.models.subject import Subject
from classes.models.term import Term
from enrollments.models.enrollment import Enrollment
from grades.models import Grade
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer
from academic.serializers.subject import SubjectMinimalSerializer
from enrollments.serializers.enrollment import EnrollmentMinimalSerializer
from teachers.models.teacher import Teacher
from teachers.serializers.teacher import TeacherMinimalSerializer
from classes.serializers.term import TermMinimalSerializer
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class GradeMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for grades."""

    student = StudentMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)

    class Meta:
        model = Grade
        fields = ["id", "student", "subject", "term", "percentage", "status"]
        read_only_fields = fields


class GradeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a grade."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source="enrollment"
    )
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )
    term_id = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all(), source="term"
    )
    graded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="graded_by", required=False, allow_null=True
    )

    class Meta:
        model = Grade
        fields = [
            "student_id", "subject_id", "enrollment_id", "teacher_id", "term_id",
            "raw_score", "percentage", "transmuted_grade", "letter_grade",
            "remarks", "graded_by_id", "status"
        ]

    def create(self, validated_data) -> Grade:
        from grades.services.grade import GradeService

        return GradeService.create_grade(**validated_data)


class GradeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a grade."""

    graded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="graded_by", required=False, allow_null=True
    )

    class Meta:
        model = Grade
        fields = ["raw_score", "percentage", "transmuted_grade", "letter_grade", "remarks", "status", "graded_by_id"]

    def update(self, instance, validated_data) -> Grade:
        from grades.services.grade import GradeService

        return GradeService.update_grade(instance, validated_data)


class GradeDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a grade."""

    student = StudentMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    enrollment = EnrollmentMinimalSerializer(read_only=True)
    teacher = TeacherMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)
    graded_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Grade
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "graded_at"]