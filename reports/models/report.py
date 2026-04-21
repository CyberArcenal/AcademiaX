from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel
from common.enums.reports import ReportType, ReportFormat, ReportStatus

class Report(TimestampedModel, UUIDModel):
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    format = models.CharField(max_length=10, choices=ReportFormat.choices, default=ReportFormat.PDF)
    status = models.CharField(max_length=10, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    parameters = models.JSONField(default=dict, help_text="Filters used (e.g., {'academic_year': '2025-2026', 'grade_level': 'G7'})")
    file_url = models.URLField(blank=True, help_text="Storage URL of generated file")
    file_size = models.PositiveIntegerField(null=True, blank=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()} ({self.generated_at})"