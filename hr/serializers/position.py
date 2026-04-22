from rest_framework import serializers
from hr.models import Position
from hr.models.department import Department


class PositionMinimalSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()

    class Meta:
        model = Position
        fields = ["id", "title", "department", "salary_grade", "is_active"]
        read_only_fields = fields

    def get_department(self, obj):
        if obj.department:
            from hr.serializers.department import DepartmentMinimalSerializer
            return DepartmentMinimalSerializer(obj.department).data
        return None


class PositionCreateSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department"
    )

    class Meta:
        model = Position
        fields = ["title", "department_id", "salary_grade"]

    def create(self, validated_data) -> Position:
        from hr.services.position import PositionService
        return PositionService.create_position(**validated_data)


class PositionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["title", "salary_grade", "is_active"]

    def update(self, instance, validated_data) -> Position:
        from hr.services.position import PositionService
        return PositionService.update_position(instance, validated_data)


class PositionDisplaySerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()

    class Meta:
        model = Position
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_department(self, obj):
        if obj.department:
            from hr.serializers.department import DepartmentMinimalSerializer
            return DepartmentMinimalSerializer(obj.department).data
        return None