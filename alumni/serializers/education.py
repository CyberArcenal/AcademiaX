from rest_framework import serializers
from alumni.models import PostGraduateEducation
from alumni.models.alumni import Alumni
from .alumni import AlumniMinimalSerializer


class PostGraduateEducationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for postgraduate education."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = PostGraduateEducation
        fields = ["id", "alumni", "degree", "institution", "year_end"]
        read_only_fields = fields


class PostGraduateEducationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a postgraduate education record."""

    alumni_id = serializers.PrimaryKeyRelatedField(
        queryset=Alumni.objects.all(), source="alumni"
    )

    class Meta:
        model = PostGraduateEducation
        fields = "__all__"

    def create(self, validated_data) -> PostGraduateEducation:
        from alumni.services.education import PostGraduateEducationService

        return PostGraduateEducationService.create_education(**validated_data)


class PostGraduateEducationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a postgraduate education record."""

    class Meta:
        model = PostGraduateEducation
        fields = ["degree", "institution", "year_end", "is_graduate", "notes"]

    def update(self, instance, validated_data) -> PostGraduateEducation:
        from alumni.services.education import PostGraduateEducationService

        return PostGraduateEducationService.update_education(instance, validated_data)


class PostGraduateEducationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a postgraduate education record."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = PostGraduateEducation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]