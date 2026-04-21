from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .student import Student

class StudentAchievement(TimestampedModel, UUIDModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    awarding_body = models.CharField(max_length=200)
    date_awarded = models.DateField()
    level = models.CharField(max_length=20, choices=[
        ('SCHOOL', 'School Level'),
        ('DISTRICT', 'District Level'),
        ('DIVISION', 'Division Level'),
        ('REGIONAL', 'Regional Level'),
        ('NATIONAL', 'National Level'),
        ('INTERNATIONAL', 'International Level'),
    ])
    description = models.TextField(blank=True)
    certificate_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-date_awarded']

    def __str__(self):
        return f"{self.student} - {self.title}"