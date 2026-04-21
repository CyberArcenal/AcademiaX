from rest_framework import serializers
from students.models import Student
from users.serializers.user.minimal import UserMinimalSerializer
from classes.serializers.grade_level import GradeLevelMinimalSerializer


class StudentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for students."""

    class Meta:
        model = Student
        fields = ["id", "student_id", "first_name", "last_name", "lrn"]
        read_only_fields = fields


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a student."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", required=False, allow_null=True
    )

    class Meta:
        model = Student
        fields = [
            "first_name", "last_name", "middle_name", "suffix", "birth_date",
            "gender", "lrn", "user_id", "current_address", "permanent_address",
            "contact_number", "personal_email"
        ]

    def create(self, validated_data) -> Student:
        from students.services.student import StudentService

        return StudentService.create_student(**validated_data)


class StudentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a student."""

    class Meta:
        model = Student
        fields = [
            "first_name", "last_name", "middle_name", "suffix", "birth_date",
            "gender", "lrn", "current_address", "permanent_address",
            "contact_number", "personal_email", "status", "profile_picture_url"
        ]

    def update(self, instance, validated_data) -> Student:
        from students.services.student import StudentService

        return StudentService.update_student(instance, validated_data)


class StudentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a student."""

    user = UserMinimalSerializer(read_only=True)
    grade_level = GradeLevelMinimalSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ["id", "student_id", "created_at", "updated_at", "enrollment_date"]

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()