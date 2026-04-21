from rest_framework import serializers
from students.models import StudentAchievement
from .student import StudentMinimalSerializer


class StudentAchievementMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for student achievements."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = StudentAchievement
        fields = ["id", "student", "title", "level", "date_awarded"]
        read_only_fields = fields


class StudentAchievementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a student achievement."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )

    class Meta:
        model = StudentAchievement
        fields = "__all__"

    def create(self, validated_data) -> StudentAchievement:
        from students.services.student_achievement import StudentAchievementService

        return StudentAchievementService.create_achievement(**validated_data)


class StudentAchievementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a student achievement."""

    class Meta:
        model = StudentAchievement
        fields = ["title", "description", "certificate_url"]

    def update(self, instance, validated_data) -> StudentAchievement:
        from students.services.student_achievement import StudentAchievementService

        return StudentAchievementService.update_achievement(instance, validated_data)


class StudentAchievementDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a student achievement."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = StudentAchievement
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]