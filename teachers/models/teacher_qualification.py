from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .teacher import Teacher

class TeacherQualification(TimestampedModel, UUIDModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='qualifications')
    qualification_name = models.CharField(max_length=200, help_text="e.g., LET Passer, Masteral Units")
    issuing_body = models.CharField(max_length=200)
    date_earned = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    attachment_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-date_earned']

    def __str__(self):
        return f"{self.teacher} - {self.qualification_name}"