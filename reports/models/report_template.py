from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.reports import ReportType

class ReportTemplate(TimestampedModel, UUIDModel):
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    template_file = models.FileField(upload_to='report_templates/')
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['report_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"