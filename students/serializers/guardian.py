from rest_framework import serializers
from students.models import Guardian
from students.models.student import Student
from .student import StudentMinimalSerializer


class GuardianMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for guardians."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = Guardian
        fields = ["id", "student", "first_name", "last_name", "relationship", "is_primary"]
        read_only_fields = fields


class GuardianCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a guardian."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )

    class Meta:
        model = Guardian
        fields = "__all__"

    def create(self, validated_data) -> Guardian:
        from students.services.guardian import GuardianService

        return GuardianService.create_guardian(**validated_data)


class GuardianUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a guardian."""

    class Meta:
        model = Guardian
        fields = [
            "first_name", "last_name", "middle_name", "relationship",
            "contact_number", "email", "occupation", "is_primary", "lives_with_student"
        ]

    def update(self, instance, validated_data) -> Guardian:
        from students.services.guardian import GuardianService

        return GuardianService.update_guardian(instance, validated_data)


class GuardianDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a guardian."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = Guardian
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]