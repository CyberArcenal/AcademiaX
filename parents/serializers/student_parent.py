from rest_framework import serializers
from parents.models import StudentParent
from parents.models.parent import Parent
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer
from .parent import ParentMinimalSerializer


class StudentParentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for student-parent relationships."""

    student = StudentMinimalSerializer(read_only=True)
    parent = ParentMinimalSerializer(read_only=True)

    class Meta:
        model = StudentParent
        fields = ["id", "student", "parent", "relationship", "is_primary_contact"]
        read_only_fields = fields


class StudentParentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a student-parent relationship."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(), source="parent"
    )

    class Meta:
        model = StudentParent
        fields = [
            "student_id", "parent_id", "relationship", "is_primary_contact",
            "can_pickup", "receives_academic_updates", "receives_disciplinary_updates",
            "receives_payment_reminders", "notes"
        ]

    def create(self, validated_data) -> StudentParent:
        from parents.services.student_parent import StudentParentService

        return StudentParentService.create_relationship(**validated_data)


class StudentParentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a student-parent relationship."""

    class Meta:
        model = StudentParent
        fields = [
            "relationship", "is_primary_contact", "can_pickup",
            "receives_academic_updates", "receives_disciplinary_updates",
            "receives_payment_reminders", "notes"
        ]

    def update(self, instance, validated_data) -> StudentParent:
        from parents.services.student_parent import StudentParentService

        return StudentParentService.update_relationship(instance, validated_data)


class StudentParentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a student-parent relationship."""

    student = StudentMinimalSerializer(read_only=True)
    parent = ParentMinimalSerializer(read_only=True)

    class Meta:
        model = StudentParent
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]