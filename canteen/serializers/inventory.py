from rest_framework import serializers
from canteen.models import InventoryLog
from .product import ProductMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class InventoryLogMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for inventory logs."""

    product = ProductMinimalSerializer(read_only=True)

    class Meta:
        model = InventoryLog
        fields = ["id", "product", "quantity_change", "new_quantity", "reason", "created_at"]
        read_only_fields = fields


class InventoryLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an inventory log."""

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )
    recorded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="recorded_by", required=False, allow_null=True
    )

    class Meta:
        model = InventoryLog
        fields = ["product_id", "quantity_change", "reason", "notes", "recorded_by_id"]

    def create(self, validated_data) -> InventoryLog:
        from canteen.services.inventory import InventoryLogService

        return InventoryLogService.create_log(**validated_data)


class InventoryLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an inventory log (notes only)."""

    class Meta:
        model = InventoryLog
        fields = ["notes"]

    def update(self, instance, validated_data) -> InventoryLog:
        from canteen.services.inventory import InventoryLogService

        # Logs typically not updated, but allow notes change
        instance.notes = validated_data.get('notes', instance.notes)
        instance.save()
        return instance


class InventoryLogDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an inventory log."""

    product = ProductMinimalSerializer(read_only=True)
    recorded_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = InventoryLog
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]