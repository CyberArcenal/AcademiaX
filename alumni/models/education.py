from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .alumni import Alumni

class PostGraduateEducation(TimestampedModel, UUIDModel):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='higher_educations')
    degree = models.CharField(max_length=200, help_text="e.g., BS Computer Science")
    institution = models.CharField(max_length=200)
    year_start = models.IntegerField()
    year_end = models.IntegerField(null=True, blank=True)
    is_graduate = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-year_end']

    def __str__(self):
        return f"{self.alumni} - {self.degree} at {self.institution}"