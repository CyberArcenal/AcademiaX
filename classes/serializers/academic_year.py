from rest_framework import serializers
from classes.models import AcademicYear


class AcademicYearMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for academic years."""

    class Meta:
        model = AcademicYear
        fields = ["id", "name", "start_date", "end_date", "is_current"]
        read_only_fields = fields


class AcademicYearCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an academic year."""

    class Meta:
        model = AcademicYear
        fields = ["name", "start_date", "end_date", "is_current"]

    def create(self, validated_data) -> AcademicYear:
        from classes.services.academic_year import AcademicYearService

        return AcademicYearService.create_academic_year(**validated_data)


class AcademicYearUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an academic year."""

    class Meta:
        model = AcademicYear
        fields = ["name", "start_date", "end_date", "is_current"]

    def update(self, instance, validated_data) -> AcademicYear:
        from classes.services.academic_year import AcademicYearService

        return AcademicYearService.update_academic_year(instance, validated_data)


class AcademicYearDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an academic year."""

    class Meta:
        model = AcademicYear
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]