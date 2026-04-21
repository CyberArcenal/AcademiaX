from django.db import models
from common.base.models import TimestampedModel
from .report import Report

class ReportLog(TimestampedModel):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50, choices=[
        ('GENERATED', 'Generated'),
        ('DOWNLOADED', 'Downloaded'),
        ('EMAILED', 'Emailed'),
        ('DELETED', 'Deleted'),
    ])
    performed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report.name} - {self.action} by {self.performed_by}"