from rest_framework import serializers
from reports.models import Report
from users.serializers.user.minimal import UserMinimalSerializer


class ReportMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for reports."""

    generated_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ["id", "name", "report_type", "format", "status", "generated_at"]
        read_only_fields = fields


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a report (usually triggered by generation)."""

    generated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="generated_by", required=False, allow_null=True
    )

    class Meta:
        model = Report
        fields = ["name", "report_type", "format", "parameters", "generated_by_id", "expires_at"]

    def create(self, validated_data) -> Report:
        from reports.services.report import ReportService

        return ReportService.create_report(**validated_data)


class ReportUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a report (status, file url)."""

    class Meta:
        model = Report
        fields = ["status", "file_url", "file_size", "error_message"]

    def update(self, instance, validated_data) -> Report:
        from reports.services.report import ReportService

        if validated_data.get('status') == 'CMP':
            return ReportService.mark_completed(instance, validated_data.get('file_url'), validated_data.get('file_size'))
        elif validated_data.get('status') == 'FLD':
            return ReportService.mark_failed(instance, validated_data.get('error_message', ''))
        return ReportService.update_report(instance, validated_data)


class ReportDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a report."""

    generated_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "generated_at"]