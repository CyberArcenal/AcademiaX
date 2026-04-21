from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.reports import ReportStatus, ReportType, ReportFormat

class ReportSchedule(TimestampedModel, UUIDModel):
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    format = models.CharField(max_length=10, choices=ReportFormat.choices, default=ReportFormat.PDF)
    parameters = models.JSONField(default=dict)
    cron_expression = models.CharField(max_length=100, help_text="e.g., '0 8 * * 1' for every Monday 8 AM")
    recipients = models.JSONField(default=list, help_text="List of email addresses")
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(max_length=10, choices=ReportStatus.choices, null=True, blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} - {self.cron_expression}"