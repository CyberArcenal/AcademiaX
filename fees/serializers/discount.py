from rest_framework import serializers
from fees.models import Discount
from classes.serializers.academic_year import AcademicYearMinimalSerializer
from classes.serializers.grade_level import GradeLevelMinimalSerializer


class DiscountMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for discounts."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)

    class Meta:
        model = Discount
        fields = ["id", "name", "discount_type", "value", "is_active"]
        read_only_fields = fields


class DiscountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a discount."""

    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year", required=False, allow_null=True
    )
    grade_level_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeLevel.objects.all(), source="grade_level", required=False, allow_null=True
    )

    class Meta:
        model = Discount
        fields = "__all__"

    def create(self, validated_data) -> Discount:
        from fees.services.discount import DiscountService

        return DiscountService.create_discount(**validated_data)


class DiscountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a discount."""

    class Meta:
        model = Discount
        fields = ["name", "value", "is_percentage", "applicable_to", "specific_category", "valid_until", "is_active"]

    def update(self, instance, validated_data) -> Discount:
        from fees.services.discount import DiscountService

        return DiscountService.update_discount(instance, validated_data)


class DiscountDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a discount."""

    academic_year = AcademicYearMinimalSerializer(read_only=True)
    grade_level = GradeLevelMinimalSerializer(read_only=True)

    class Meta:
        model = Discount
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]