from rest_framework import serializers
from canteen.models import Category


class CategoryMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for categories."""

    class Meta:
        model = Category
        fields = ["id", "name", "display_order"]
        read_only_fields = fields


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a category."""

    class Meta:
        model = Category
        fields = ["name", "display_order", "description"]

    def create(self, validated_data) -> Category:
        from canteen.services.category import CategoryService

        return CategoryService.create_category(**validated_data)


class CategoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a category."""

    class Meta:
        model = Category
        fields = ["name", "display_order", "description", "is_active"]

    def update(self, instance, validated_data) -> Category:
        from canteen.services.category import CategoryService

        return CategoryService.update_category(instance, validated_data)


class CategoryDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a category."""

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]