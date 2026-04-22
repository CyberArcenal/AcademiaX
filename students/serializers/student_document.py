from rest_framework import serializers
from students.models import StudentDocument
from students.models.student import Student
from users.models.user import User
from .student import StudentMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class StudentDocumentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for student documents."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = StudentDocument
        fields = ["id", "student", "document_type", "title", "verified"]
        read_only_fields = fields


class StudentDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a student document."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    uploaded_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="uploaded_by", required=False, allow_null=True
    )

    class Meta:
        model = StudentDocument
        fields = "__all__"

    def create(self, validated_data) -> StudentDocument:
        from students.services.student_document import StudentDocumentService

        return StudentDocumentService.create_document(**validated_data)


class StudentDocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a student document."""

    class Meta:
        model = StudentDocument
        fields = ["title", "notes", "expiry_date"]

    def update(self, instance, validated_data) -> StudentDocument:
        from students.services.student_document import StudentDocumentService

        return StudentDocumentService.update_document(instance, validated_data)


class StudentDocumentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a student document."""

    student = StudentMinimalSerializer(read_only=True)
    uploaded_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = StudentDocument
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "verified_at"]