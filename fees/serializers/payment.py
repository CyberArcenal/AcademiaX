from rest_framework import serializers
from fees.models import Payment
from .fee_assessment import FeeAssessmentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class PaymentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for payments."""

    assessment = FeeAssessmentMinimalSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "assessment", "amount", "payment_date", "payment_method", "reference_number"]
        read_only_fields = fields


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a payment."""

    assessment_id = serializers.PrimaryKeyRelatedField(
        queryset=FeeAssessment.objects.all(), source="assessment"
    )
    received_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="received_by", required=False, allow_null=True
    )

    class Meta:
        model = Payment
        fields = ["assessment_id", "amount", "payment_date", "payment_method", "reference_number", "check_number", "bank_name", "received_by_id", "notes"]

    def create(self, validated_data) -> Payment:
        from fees.services.payment import PaymentService

        return PaymentService.process_payment(**validated_data)


class PaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a payment (e.g., verify)."""

    class Meta:
        model = Payment
        fields = ["is_verified", "notes"]

    def update(self, instance, validated_data) -> Payment:
        from fees.services.payment import PaymentService

        if validated_data.get('is_verified') and not instance.is_verified:
            return PaymentService.verify_payment(instance)
        return PaymentService.update_payment(instance, validated_data)


class PaymentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a payment."""

    assessment = FeeAssessmentMinimalSerializer(read_only=True)
    received_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]