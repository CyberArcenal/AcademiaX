from rest_framework import serializers
from alumni.models import Employment
from .alumni import AlumniMinimalSerializer


class EmploymentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for employment records."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = Employment
        fields = ["id", "alumni", "job_title", "company_name", "is_current"]
        read_only_fields = fields


class EmploymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an employment record."""

    alumni_id = serializers.PrimaryKeyRelatedField(
        queryset=Alumni.objects.all(), source="alumni"
    )

    class Meta:
        model = Employment
        fields = "__all__"

    def create(self, validated_data) -> Employment:
        from alumni.services.employment import EmploymentService

        return EmploymentService.create_employment(**validated_data)


class EmploymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an employment record."""

    class Meta:
        model = Employment
        fields = [
            "job_title", "company_name", "employment_type", "end_date",
            "is_current", "location", "industry"
        ]

    def update(self, instance, validated_data) -> Employment:
        from alumni.services.employment import EmploymentService

        return EmploymentService.update_employment(instance, validated_data)


class EmploymentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an employment record."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = Employment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]