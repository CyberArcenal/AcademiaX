from rest_framework import serializers
from canteen.models import Product
from .category import CategoryMinimalSerializer


class ProductMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for products."""

    category = CategoryMinimalSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "category", "price", "is_available", "stock_quantity"]
        read_only_fields = fields


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a product."""

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category"
    )

    class Meta:
        model = Product
        fields = "__all__"

    def create(self, validated_data) -> Product:
        from canteen.services.product import ProductService

        return ProductService.create_product(**validated_data)


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a product."""

    class Meta:
        model = Product
        fields = [
            "name", "description", "price", "cost", "stock_quantity",
            "is_available", "preparation_time_minutes", "is_vegetarian",
            "is_gluten_free", "image_url"
        ]

    def update(self, instance, validated_data) -> Product:
        from canteen.services.product import ProductService

        return ProductService.update_product(instance, validated_data)


class ProductDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a product."""

    category = CategoryMinimalSerializer(read_only=True)

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]