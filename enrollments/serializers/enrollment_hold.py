from rest_framework import serializers
from enrollments.models import EnrollmentHold
from .enrollment import EnrollmentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class EnrollmentHoldMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for enrollment holds."""

    enrollment = EnrollmentMinimalSerializer(read_only=True)

    class Meta:
        model = EnrollmentHold
        fields = ["id", "enrollment", "reason", "amount_due", "is_resolved"]
        read_only_fields = fields


class EnrollmentHoldCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an enrollment hold."""

    enrollment_id = serializers.PrimaryKeyRelatedField(
        queryset=Enrollment.objects.all(), source="enrollment"
    )

    class Meta:
        model = EnrollmentHold
        fields = ["enrollment_id", "reason", "amount_due"]

    def create(self, validated_data) -> EnrollmentHold:
        from enrollments.services.enrollment_hold import EnrollmentHoldService

        return EnrollmentHoldService.create_hold(**validated_data)


class EnrollmentHoldUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an enrollment hold (resolve, edit)."""

    resolved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="resolved_by", required=False, allow_null=True
    )

    class Meta:
        model = EnrollmentHold
        fields = ["reason", "amount_due", "is_resolved", "resolved_by_id"]

    def update(self, instance, validated_data) -> EnrollmentHold:
        from enrollments.services.enrollment_hold import EnrollmentHoldService

        if validated_data.get('is_resolved') and not instance.is_resolved:
            return EnrollmentHoldService.resolve_hold(instance, validated_data.get('resolved_by'))
        return EnrollmentHoldService.update_hold(instance, validated_data.get('reason', instance.reason), validated_data.get('amount_due', instance.amount_due))


class EnrollmentHoldDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an enrollment hold."""

    enrollment = EnrollmentMinimalSerializer(read_only=True)
    resolved_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = EnrollmentHold
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "resolved_at"]