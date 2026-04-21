from rest_framework import serializers
from alumni.models import Donation
from .alumni import AlumniMinimalSerializer


class DonationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for donations."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = ["id", "alumni", "amount", "date", "purpose"]
        read_only_fields = fields


class DonationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a donation record."""

    alumni_id = serializers.PrimaryKeyRelatedField(
        queryset=Alumni.objects.all(), source="alumni"
    )

    class Meta:
        model = Donation
        fields = "__all__"

    def create(self, validated_data) -> Donation:
        from alumni.services.donation import DonationService

        return DonationService.create_donation(**validated_data)


class DonationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a donation record."""

    class Meta:
        model = Donation
        fields = ["receipt_number", "remarks"]

    def update(self, instance, validated_data) -> Donation:
        from alumni.services.donation import DonationService

        return DonationService.update_donation(instance, validated_data)


class DonationDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a donation record."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]