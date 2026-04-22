from rest_framework import serializers
from hr.models import Department
from hr.models.employee import Employee


class DepartmentCreateSerializer(serializers.ModelSerializer):
    head_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="head", required=False, allow_null=True
    )

    class Meta:
        model = Department
        fields = ["name", "code", "description", "head_id"]

    def create(self, validated_data) -> Department:
        from hr.services.department import DepartmentService
        return DepartmentService.create_department(**validated_data)


class DepartmentUpdateSerializer(serializers.ModelSerializer):
    head_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="head", required=False, allow_null=True
    )

    class Meta:
        model = Department
        fields = ["name", "code", "description", "head_id", "is_active"]

    def update(self, instance, validated_data) -> Department:
        from hr.services.department import DepartmentService
        return DepartmentService.update_department(instance, validated_data)


class DepartmentMinimalSerializer(serializers.ModelSerializer):
    head = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "code", "head", "is_active"]
        read_only_fields = fields

    def get_head(self, obj):
        if obj.head:
            from hr.serializers.employee import EmployeeMinimalSerializer
            return EmployeeMinimalSerializer(obj.head).data
        return None


class DepartmentDisplaySerializer(serializers.ModelSerializer):
    head = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_head(self, obj):
        if obj.head:
            from hr.serializers.employee import EmployeeMinimalSerializer
            return EmployeeMinimalSerializer(obj.head).data
        return None