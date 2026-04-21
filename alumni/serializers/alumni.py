from rest_framework import serializers
from alumni.models import Alumni
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class AlumniMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for alumni."""

    student = StudentMinimalSerializer(read_only=True)
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Alumni
        fields = ["id", "student", "user", "graduation_year", "batch"]
        read_only_fields = fields


class AlumniCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an alumni record."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student", required=False, allow_null=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", required=False, allow_null=True
    )

    class Meta:
        model = Alumni
        fields = [
            "student_id", "user_id", "graduation_year", "batch",
            "current_city", "current_country", "contact_number",
            "personal_email", "facebook_url", "linkedin_url"
        ]

    def create(self, validated_data) -> Alumni:
        from alumni.services.alumni import AlumniService

        return AlumniService.create_alumni(**validated_data)


class AlumniUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an alumni record."""

    class Meta:
        model = Alumni
        fields = [
            "current_city", "current_country", "contact_number",
            "personal_email", "facebook_url", "linkedin_url", "is_active"
        ]

    def update(self, instance, validated_data) -> Alumni:
        from alumni.services.alumni import AlumniService

        return AlumniService.update_alumni(instance, validated_data)


class AlumniDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an alumni record."""

    student = StudentMinimalSerializer(read_only=True)
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Alumni
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]