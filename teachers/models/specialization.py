from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from .teacher import Teacher

class Specialization(TimestampedModel, UUIDModel, SoftDeleteModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='specializations')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE, related_name='specialized_teachers')
    is_primary = models.BooleanField(default=False)
    proficiency_level = models.CharField(max_length=20, choices=[
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    ])

    class Meta:
        unique_together = [['teacher', 'subject']]

    def __str__(self):
        return f"{self.teacher} specializes in {self.subject.code}"