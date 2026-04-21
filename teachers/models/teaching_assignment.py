from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .teacher import Teacher

class TeachingAssignment(TimestampedModel, UUIDModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments')
    section = models.ForeignKey('classes.Section', on_delete=models.CASCADE, related_name='teacher_assignments')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE, related_name='teacher_assignments')
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE)
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['teacher', 'section', 'subject', 'academic_year']]

    def __str__(self):
        return f"{self.teacher} teaches {self.subject.code} to {self.section}"