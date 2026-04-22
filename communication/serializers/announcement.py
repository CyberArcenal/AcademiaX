from rest_framework import serializers
from classes.models.grade_level import GradeLevel
from classes.models.section import Section
from communication.models import Announcement
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer
from classes.serializers.grade_level import GradeLevelMinimalSerializer
from classes.serializers.section import SectionMinimalSerializer


class AnnouncementMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for announcements."""

    author = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Announcement
        fields = ["id", "title", "author", "published_at", "target_audience"]
        read_only_fields = fields


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an announcement."""

    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="author"
    )
    grade_level_id = serializers.PrimaryKeyRelatedField(
        queryset=GradeLevel.objects.all(), source="grade_level", required=False, allow_null=True
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section", required=False, allow_null=True
    )

    class Meta:
        model = Announcement
        fields = [
            "title", "content", "author_id", "target_audience", "grade_level_id",
            "section_id", "channels", "scheduled_at", "expires_at", "attachment_urls"
        ]

    def create(self, validated_data) -> Announcement:
        from communication.services.announcement import AnnouncementService

        return AnnouncementService.create_announcement(**validated_data)


class AnnouncementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an announcement."""

    class Meta:
        model = Announcement
        fields = ["title", "content", "target_audience", "channels", "expires_at", "attachment_urls"]

    def update(self, instance, validated_data) -> Announcement:
        from communication.services.announcement import AnnouncementService

        return AnnouncementService.update_announcement(instance, validated_data)


class AnnouncementDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an announcement."""

    author = UserMinimalSerializer(read_only=True)
    grade_level = GradeLevelMinimalSerializer(read_only=True)
    section = SectionMinimalSerializer(read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "published_at"]