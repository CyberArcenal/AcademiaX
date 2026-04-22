from rest_framework import serializers
from classes.models.term import Term
from enrollments.models.enrollment import Enrollment
from fees.models import FeeAssessment
from enrollments.serializers.enrollment import EnrollmentMinimalSerializer
from fees.models.fee_structure import FeeStructure
from .fee_structure import FeeStructureMinimalSerializer
from classes.serializers.term import TermMinimalSerializer


class FeeAssessmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for fee assessments."""

    enrollment = EnrollmentMinimalSerializer(read_only=True)
    fee_structure = FeeStructureMinimalSerializer(read_only=True)

    class Meta:
        model = FeeAssessment
        fields = ["id", "enrollment", "fee_structure", "amount", "due_date", "status", "balance"]
        read_only_fields = fields


class FeeAssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a fee assessment."""

    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source="enrollment"
    )
    fee_structure_id = serializers.PrimaryKeyRelatedField(
        queryset=FeeStructure.objects.all(), source="fee_structure"
    )
    term_id = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all(), source="term", required=False, allow_null=True
    )

    class Meta:
        model = FeeAssessment
        fields = ["enrollment_id", "fee_structure_id", "amount", "due_date", "term_id", "remarks"]

    def create(self, validated_data) -> FeeAssessment:
        from fees.services.fee_assessment import FeeAssessmentService

        return FeeAssessmentService.create_assessment(**validated_data)


class FeeAssessmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a fee assessment (e.g., adjust amount)."""

    class Meta:
        model = FeeAssessment
        fields = ["amount", "due_date", "remarks"]

    def update(self, instance, validated_data) -> FeeAssessment:
        from fees.services.fee_assessment import FeeAssessmentService

        return FeeAssessmentService.update_assessment(instance, validated_data)


class FeeAssessmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a fee assessment."""

    enrollment = EnrollmentMinimalSerializer(read_only=True)
    fee_structure = FeeStructureMinimalSerializer(read_only=True)
    term = TermMinimalSerializer(read_only=True)

    class Meta:
        model = FeeAssessment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]