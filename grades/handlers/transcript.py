from django.db import models
from common.base.models import TimestampedModel, UUIDModel

class Transcript(TimestampedModel, UUIDModel):
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='transcript')
    cumulative_gwa = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_units_completed = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    graduation_date = models.DateField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_url = models.URLField(blank=True)
    is_official = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Transcript - {self.student}"