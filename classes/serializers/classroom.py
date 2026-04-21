from rest_framework import serializers
from classes.models import Classroom


class ClassroomMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for classrooms."""

    class Meta:
        model = Classroom
        fields = ["id", "room_number", "building", "capacity"]
        read_only_fields = fields


class ClassroomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a classroom."""

    class Meta:
        model = Classroom
        fields = ["room_number", "building", "floor", "capacity", "room_type", "has_projector", "has_aircon"]

    def create(self, validated_data) -> Classroom:
        from classes.services.classroom import ClassroomService

        return ClassroomService.create_classroom(**validated_data)


class ClassroomUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a classroom."""

    class Meta:
        model = Classroom
        fields = ["room_number", "building", "floor", "capacity", "room_type", "has_projector", "has_aircon", "is_active"]

    def update(self, instance, validated_data) -> Classroom:
        from classes.services.classroom import ClassroomService

        return ClassroomService.update_classroom(instance, validated_data)


class ClassroomDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a classroom."""

    class Meta:
        model = Classroom
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]