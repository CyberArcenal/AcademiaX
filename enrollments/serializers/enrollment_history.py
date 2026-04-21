from rest_framework import serializers
from enrollments.models import EnrollmentHistory
from .enrollment import EnrollmentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class EnrollmentHistoryMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for enrollment history."""

    enrollment = EnrollmentMinimalSerializer(read_only=True)

    class Meta:
        model = EnrollmentHistory
        fields = ["id", "enrollment", "previous_status", "new_status", "created_at"]
        read_only_fields = fields


class EnrollmentHistoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an enrollment history entry (usually internal)."""

    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source="enrollment"
    )
    changed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="changed_by", required=False, allow_null=True
    )

    class Meta:
        model = EnrollmentHistory
        fields = ["enrollment_id", "previous_status", "new_status", "reason", "remarks", "changed_by_id"]

    def create(self, validated_data) -> EnrollmentHistory:
        from enrollments.services.enrollment_history import EnrollmentHistoryService

        return EnrollmentHistoryService.create_history(**validated_data)


class EnrollmentHistoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an enrollment history (not typically allowed)."""

    class Meta:
        model = EnrollmentHistory
        fields = []  # No updates

    def update(self, instance, validated_data) -> EnrollmentHistory:
        return instance


class EnrollmentHistoryDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an enrollment history entry."""

    enrollment = EnrollmentMinimalSerializer(read_only=True)
    changed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = EnrollmentHistory
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]