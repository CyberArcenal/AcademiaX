from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.alumni import EmploymentType
from .alumni import Alumni

class Employment(TimestampedModel, UUIDModel):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='employments')
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=10, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.alumni} - {self.job_title} at {self.company_name}"