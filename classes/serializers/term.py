from rest_framework import serializers
from classes.models import Term
from .academic_year import AcademicYearMinimalSerializer


class TermMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for terms."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = Term
        fields = ["id", "academic_year", "name", "term_number", "is_active"]
        read_only_fields = fields


class TermCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a term."""

    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )

    class Meta:
        model = Term
        fields = ["academic_year_id", "term_type", "term_number", "name", "start_date", "end_date", "is_active"]

    def create(self, validated_data) -> Term:
        from classes.services.term import TermService

        return TermService.create_term(**validated_data)


class TermUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a term."""

    class Meta:
        model = Term
        fields = ["name", "start_date", "end_date", "is_active"]

    def update(self, instance, validated_data) -> Term:
        from classes.services.term import TermService

        return TermService.update_term(instance, validated_data)


class TermDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a term."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = Term
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]