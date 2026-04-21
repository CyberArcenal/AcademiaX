from rest_framework import serializers
from reports.models import ReportSchedule
from users.serializers.user.minimal import UserMinimalSerializer


class ReportScheduleMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for report schedules."""

    created_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReportSchedule
        fields = ["id", "name", "report_type", "cron_expression", "is_active", "last_run_at"]
        read_only_fields = fields


class ReportScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a report schedule."""

    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="created_by", required=False, allow_null=True
    )

    class Meta:
        model = ReportSchedule
        fields = ["name", "report_type", "format", "parameters", "cron_expression", "recipients", "created_by_id"]

    def create(self, validated_data) -> ReportSchedule:
        from reports.services.report_schedule import ReportScheduleService

        return ReportScheduleService.create_schedule(**validated_data)


class ReportScheduleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a report schedule."""

    class Meta:
        model = ReportSchedule
        fields = ["name", "cron_expression", "recipients", "is_active"]

    def update(self, instance, validated_data) -> ReportSchedule:
        from reports.services.report_schedule import ReportScheduleService

        return ReportScheduleService.update_schedule(instance, validated_data)


class ReportScheduleDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a report schedule."""

    created_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReportSchedule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]