from rest_framework import serializers
from fees.models import CollectionReport
from users.serializers.user.minimal import UserMinimalSerializer


class CollectionReportMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for collection reports."""

    generated_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = CollectionReport
        fields = ["id", "report_date", "total_collections", "generated_by"]
        read_only_fields = fields


class CollectionReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a collection report (usually auto-generated)."""

    generated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="generated_by", required=False, allow_null=True
    )

    class Meta:
        model = CollectionReport
        fields = ["report_date", "generated_by_id", "notes"]

    def create(self, validated_data) -> CollectionReport:
        from fees.services.collection import CollectionReportService

        return CollectionReportService.generate_daily_report(**validated_data)


class CollectionReportUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a collection report (notes only)."""

    class Meta:
        model = CollectionReport
        fields = ["notes"]

    def update(self, instance, validated_data) -> CollectionReport:
        from fees.services.collection import CollectionReportService

        instance.notes = validated_data.get('notes', instance.notes)
        instance.save()
        return instance


class CollectionReportDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a collection report."""

    generated_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = CollectionReport
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]