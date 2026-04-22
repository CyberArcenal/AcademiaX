from rest_framework import serializers
from fees.models import Scholarship
from fees.models.discount import Discount
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer
from users.models.user import User
from .discount import DiscountMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class ScholarshipMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for scholarships."""

    student = StudentMinimalSerializer(read_only=True)
    discount = DiscountMinimalSerializer(read_only=True)

    class Meta:
        model = Scholarship
        fields = ["id", "student", "discount", "scholarship_type", "awarded_date"]
        read_only_fields = fields


class ScholarshipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a scholarship."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )
    discount_id = serializers.PrimaryKeyRelatedField(
        queryset=Discount.objects.all(), source="discount"
    )
    approved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="approved_by", required=False, allow_null=True
    )

    class Meta:
        model = Scholarship
        fields = ["student_id", "discount_id", "scholarship_type", "awarded_date", "expiry_date", "is_renewable", "grantor", "terms", "approved_by_id"]

    def create(self, validated_data) -> Scholarship:
        from fees.services.scholarship import ScholarshipService

        return ScholarshipService.create_scholarship(**validated_data)


class ScholarshipUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a scholarship (renew, expiry)."""

    class Meta:
        model = Scholarship
        fields = ["expiry_date", "is_renewable", "terms"]

    def update(self, instance, validated_data) -> Scholarship:
        from fees.services.scholarship import ScholarshipService

        if 'expiry_date' in validated_data:
            return ScholarshipService.renew_scholarship(instance, validated_data['expiry_date'])
        return ScholarshipService.update_scholarship(instance, validated_data)


class ScholarshipDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a scholarship."""

    student = StudentMinimalSerializer(read_only=True)
    discount = DiscountMinimalSerializer(read_only=True)
    approved_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Scholarship
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]