from rest_framework import serializers
from library.models import Fine
from .borrow import BorrowTransactionMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class FineMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for fines."""

    borrow_transaction = BorrowTransactionMinimalSerializer(read_only=True)

    class Meta:
        model = Fine
        fields = ["id", "borrow_transaction", "amount", "status"]
        read_only_fields = fields


class FineCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a fine (usually auto-created on overdue)."""

    borrow_transaction_id = serializers.PrimaryKeyRelatedField(
        queryset=BorrowTransaction.objects.all(), source="borrow_transaction"
    )

    class Meta:
        model = Fine
        fields = ["borrow_transaction_id", "amount", "days_overdue"]

    def create(self, validated_data) -> Fine:
        from library.services.fine import FineService

        return FineService.create_fine(**validated_data)


class FineUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a fine (pay, waive)."""

    paid_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="paid_by", required=False, allow_null=True
    )

    class Meta:
        model = Fine
        fields = ["status", "paid_by_id", "receipt_number", "remarks"]

    def update(self, instance, validated_data) -> Fine:
        from library.services.fine import FineService

        if validated_data.get('status') == 'PD':
            return FineService.pay_fine(instance, validated_data.get('paid_by'), validated_data.get('receipt_number', ''), validated_data.get('remarks', ''))
        elif validated_data.get('status') == 'WVD':
            return FineService.waive_fine(instance, validated_data.get('remarks', ''))
        return instance


class FineDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a fine."""

    borrow_transaction = BorrowTransactionMinimalSerializer(read_only=True)
    paid_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Fine
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "paid_at"]