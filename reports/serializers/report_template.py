from rest_framework import serializers
from reports.models import ReportTemplate
from users.serializers.user.minimal import UserMinimalSerializer


class ReportTemplateMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for report templates."""

    created_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReportTemplate
        fields = ["id", "name", "report_type", "is_default", "is_active"]
        read_only_fields = fields


class ReportTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a report template."""

    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="created_by", required=False, allow_null=True
    )

    class Meta:
        model = ReportTemplate
        fields = ["name", "report_type", "template_file", "description", "is_default", "created_by_id"]

    def create(self, validated_data) -> ReportTemplate:
        from reports.services.report_template import ReportTemplateService

        return ReportTemplateService.create_template(**validated_data)


class ReportTemplateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a report template."""

    class Meta:
        model = ReportTemplate
        fields = ["name", "description", "is_default", "is_active"]

    def update(self, instance, validated_data) -> ReportTemplate:
        from reports.services.report_template import ReportTemplateService

        return ReportTemplateService.update_template(instance, validated_data)


class ReportTemplateDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a report template."""

    created_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReportTemplate
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]