from rest_framework import serializers
from grades.models import ReportCard
from students.serializers.student import StudentMinimalSerializer
from classes.serializers.academic_year import AcademicYearMinimalSerializer
from classes.serializers.term import TermMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class ReportCardMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for report cards."""

    student = StudentMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)

    class Meta:
        model = ReportCard
        fields = ["id", "student", "academic_year", "term", "gpa", "generated_at"]
        read_only_fields = fields


class ReportCardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a report card."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    term_id = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all(), source="term"
    )
    signed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="signed_by", required=False, allow_null=True
    )

    class Meta:
        model = ReportCard
        fields = [
            "student_id", "academic_year_id", "term_id", "gpa", "total_units_earned",
            "honors", "signed_by_id", "notes", "pdf_url"
        ]

    def create(self, validated_data) -> ReportCard:
        from grades.services.report_card import ReportCardService

        return ReportCardService.create_report_card(**validated_data)


class ReportCardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a report card."""

    signed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="signed_by", required=False, allow_null=True
    )

    class Meta:
        model = ReportCard
        fields = ["gpa", "total_units_earned", "honors", "signed_by_id", "notes", "pdf_url"]

    def update(self, instance, validated_data) -> ReportCard:
        from grades.services.report_card import ReportCardService

        return ReportCardService.update_report_card(instance, validated_data)


class ReportCardDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a report card."""

    student = StudentMinimalSerializer(read_only=True)
    academic_year = AcademicYearMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)
    signed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReportCard
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "generated_at"]