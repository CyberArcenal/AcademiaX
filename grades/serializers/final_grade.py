from rest_framework import serializers
from grades.models import FinalGrade
from students.serializers.student import StudentMinimalSerializer
from academic.serializers.subject import SubjectMinimalSerializer
from enrollments.serializers.enrollment import EnrollmentMinimalSerializer
from classes.serializers.academic_year import AcademicYearMinimalSerializer


class FinalGradeMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for final grades."""

    student = StudentMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = FinalGrade
        fields = ["id", "student", "subject", "final_grade", "status"]
        read_only_fields = fields


class FinalGradeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a final grade."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source="enrollment"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )

    class Meta:
        model = FinalGrade
        fields = [
            "student_id", "subject_id", "enrollment_id", "academic_year_id",
            "q1_grade", "q2_grade", "q3_grade", "q4_grade", "final_grade",
            "remarks", "status"
        ]

    def create(self, validated_data) -> FinalGrade:
        from grades.services.final_grade import FinalGradeService

        return FinalGradeService.create_final_grade(**validated_data)


class FinalGradeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a final grade."""

    class Meta:
        model = FinalGrade
        fields = ["q1_grade", "q2_grade", "q3_grade", "q4_grade", "final_grade", "remarks", "status"]

    def update(self, instance, validated_data) -> FinalGrade:
        from grades.services.final_grade import FinalGradeService

        return FinalGradeService.update_final_grade(instance, validated_data)


class FinalGradeDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a final grade."""

    student = StudentMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)
    enrollment = EnrollmentMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = FinalGrade
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]