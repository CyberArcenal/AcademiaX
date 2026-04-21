from rest_framework import serializers
from reports.models import ReportLog
from .report import ReportMinimalSerializer
from users.serializers.user.minimal import UserMinimalSerializer


class ReportLogMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for report logs."""

    report = ReportMinimalSerializer(read_only=True)
    performed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReportLog
        fields = ["id", "report", "action", "performed_by", "created_at"]
        read_only_fields = fields


class ReportLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a report log (usually internal)."""

    report_id = serializers.PrimaryKeyRelatedField(
        queryset=Report.objects.all(), source="report"
    )
    performed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="performed_by", required=False, allow_null=True
    )

    class Meta:
        model = ReportLog
        fields = ["report_id", "action", "performed_by_id", "ip_address", "user_agent", "details"]

    def create(self, validated_data) -> ReportLog:
        from reports.services.report_log import ReportLogService

        return ReportLogService.create_log(**validated_data)


class ReportLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a report log (not typically allowed)."""

    class Meta:
        model = ReportLog
        fields = []  # No updates

    def update(self, instance, validated_data) -> ReportLog:
        return instance


class ReportLogDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a report log."""

    report = ReportMinimalSerializer(read_only=True)
    performed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReportLog
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]