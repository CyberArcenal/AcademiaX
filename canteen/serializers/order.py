from rest_framework import serializers
from canteen.models import Order
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer
from users.models.user import User
from users.serializers.user.minimal import UserMinimalSerializer


class OrderMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for orders."""

    student = StudentMinimalSerializer(read_only=True)
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "order_number", "student", "user", "status", "total_amount", "created_at"]
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an order."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student", required=False, allow_null=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", required=False, allow_null=True
    )
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="created_by", required=False, allow_null=True
    )

    class Meta:
        model = Order
        fields = ["order_type", "student_id", "user_id", "notes", "created_by_id"]

    def create(self, validated_data) -> Order:
        from canteen.services.order import OrderService

        return OrderService.create_order(**validated_data)


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an order (status, etc.)."""

    class Meta:
        model = Order
        fields = ["status", "notes", "prepared_by"]

    def update(self, instance, validated_data) -> Order:
        from canteen.services.order import OrderService

        if 'status' in validated_data:
            return OrderService.update_order_status(instance, validated_data['status'], validated_data.get('prepared_by'))
        return OrderService.update_order(instance, validated_data)


class OrderDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an order."""

    student = StudentMinimalSerializer(read_only=True)
    user = UserMinimalSerializer(read_only=True)
    prepared_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["id", "order_number", "created_at", "updated_at"]