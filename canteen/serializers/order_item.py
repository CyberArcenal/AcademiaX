from rest_framework import serializers
from canteen.models import OrderItem
from .order import OrderMinimalSerializer
from .product import ProductMinimalSerializer


class OrderItemMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for order items."""

    product = ProductMinimalSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "subtotal"]
        read_only_fields = fields


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding an item to an order."""

    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), source="order"
    )
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )

    class Meta:
        model = OrderItem
        fields = ["order_id", "product_id", "quantity", "special_instructions"]

    def create(self, validated_data) -> OrderItem:
        from canteen.services.order_item import OrderItemService

        return OrderItemService.add_item_to_order(**validated_data)


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an order item (quantity)."""

    class Meta:
        model = OrderItem
        fields = ["quantity"]

    def update(self, instance, validated_data) -> OrderItem:
        from canteen.services.order_item import OrderItemService

        return OrderItemService.update_quantity(instance, validated_data.get('quantity'))


class OrderItemDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an order item."""

    order = OrderMinimalSerializer(read_only=True)
    product = ProductMinimalSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "subtotal"]