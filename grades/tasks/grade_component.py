from django.db import models
from common.base.models import TimestampedModel, UUIDModel

class GradeComponent(TimestampedModel, UUIDModel):
    """Defines how grades are computed (e.g., Written Work: 40%, Performance: 40%, Exam: 20%)"""
    name = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage weight (e.g., 40.00)")
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE, related_name='grade_components')
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE, related_name='grade_components')
    grade_level = models.ForeignKey('classes.GradeLevel', on_delete=models.CASCADE, related_name='grade_components')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['subject', 'academic_year', 'grade_level', 'name']]

    def __str__(self):
        return f"{self.subject.code} - {self.name} ({self.weight}%)"