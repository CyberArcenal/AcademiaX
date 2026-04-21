from rest_framework import serializers
from alumni.models import AlumniAchievement
from alumni.models.alumni import Alumni
from .alumni import AlumniMinimalSerializer


class AlumniAchievementMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for alumni achievements."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = AlumniAchievement
        fields = ["id", "alumni", "title", "date_received"]
        read_only_fields = fields


class AlumniAchievementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an alumni achievement record."""

    alumni_id = serializers.PrimaryKeyRelatedField(
        queryset=Alumni.objects.all(), source="alumni"
    )

    class Meta:
        model = AlumniAchievement
        fields = "__all__"

    def create(self, validated_data) -> AlumniAchievement:
        from alumni.services.achievement import AlumniAchievementService

        return AlumniAchievementService.create_achievement(**validated_data)


class AlumniAchievementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an alumni achievement record."""

    class Meta:
        model = AlumniAchievement
        fields = ["title", "description", "certificate_url"]

    def update(self, instance, validated_data) -> AlumniAchievement:
        from alumni.services.achievement import AlumniAchievementService

        return AlumniAchievementService.update_achievement(instance, validated_data)


class AlumniAchievementDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an alumni achievement record."""

    alumni = AlumniMinimalSerializer(read_only=True)

    class Meta:
        model = AlumniAchievement
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]