from rest_framework import serializers
from attendance.models import Holiday


class HolidayMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for holidays."""

    class Meta:
        model = Holiday
        fields = ["id", "name", "date"]
        read_only_fields = fields


class HolidayCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a holiday."""

    class Meta:
        model = Holiday
        fields = "__all__"

    def create(self, validated_data) -> Holiday:
        from attendance.services.holiday import HolidayService

        return HolidayService.create_holiday(**validated_data)


class HolidayUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a holiday."""

    class Meta:
        model = Holiday
        fields = ["name", "date", "is_school_wide", "notes"]

    def update(self, instance, validated_data) -> Holiday:
        from attendance.services.holiday import HolidayService

        return HolidayService.update_holiday(instance, validated_data)


class HolidayDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a holiday."""

    class Meta:
        model = Holiday
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]