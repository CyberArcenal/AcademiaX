from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .alumni import Alumni

class AlumniAchievement(TimestampedModel, UUIDModel):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200, help_text="e.g., Top 10 Under 40, Best Thesis Award")
    awarding_body = models.CharField(max_length=200)
    date_received = models.DateField()
    description = models.TextField(blank=True)
    certificate_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-date_received']

    def __str__(self):
        return f"{self.alumni} - {self.title}"