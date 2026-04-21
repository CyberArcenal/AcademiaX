from rest_framework import serializers
from canteen.models import PaymentTransaction
from .order import OrderMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class PaymentTransactionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for payment transactions."""

    order = OrderMinimalSerializer(read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = ["id", "order", "amount_paid", "change_due", "payment_method", "paid_at"]
        read_only_fields = fields


class PaymentTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a payment transaction."""

    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), source="order"
    )
    received_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="received_by", required=False, allow_null=True
    )

    class Meta:
        model = PaymentTransaction
        fields = ["order_id", "amount_paid", "payment_method", "reference_number", "received_by_id", "notes"]

    def create(self, validated_data) -> PaymentTransaction:
        from canteen.services.transaction import PaymentTransactionService

        return PaymentTransactionService.process_payment(**validated_data)


class PaymentTransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a payment transaction (e.g., reference number)."""

    class Meta:
        model = PaymentTransaction
        fields = ["reference_number", "notes"]

    def update(self, instance, validated_data) -> PaymentTransaction:
        from canteen.services.transaction import PaymentTransactionService

        return PaymentTransactionService.update_transaction(instance, validated_data)


class PaymentTransactionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a payment transaction."""

    order = OrderMinimalSerializer(read_only=True)
    received_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "paid_at"]