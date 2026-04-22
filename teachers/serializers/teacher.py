from rest_framework import serializers
from teachers.models import Teacher
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class TeacherMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for teachers."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "teacher_id", "user", "first_name", "last_name"]
        read_only_fields = fields


class TeacherCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a teacher."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user"
    )

    class Meta:
        model = Teacher
        fields = [
            "user_id", "first_name", "last_name", "middle_name", "suffix",
            "gender", "birth_date", "contact_number", "personal_email",
            "teacher_type", "highest_degree", "hire_date", "years_of_experience",
            "profile_picture_url"
        ]

    def create(self, validated_data) -> Teacher:
        from teachers.services.teacher import TeacherService

        return TeacherService.create_teacher(**validated_data)


class TeacherUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a teacher."""

    class Meta:
        model = Teacher
        fields = [
            "first_name", "last_name", "middle_name", "suffix",
            "contact_number", "personal_email", "teacher_type",
            "highest_degree", "years_of_experience", "status",
            "profile_picture_url"
        ]

    def update(self, instance, validated_data) -> Teacher:
        from teachers.services.teacher import TeacherService

        return TeacherService.update_teacher(instance, validated_data)


class TeacherDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a teacher."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = "__all__"
        read_only_fields = ["id", "teacher_id", "created_at", "updated_at"]