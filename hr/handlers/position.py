from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from hr.models.department import Department

class Position(TimestampedModel, UUIDModel, SoftDeleteModel):
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    salary_grade = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['title', 'department']]
        ordering = ['department', 'title']

    def __str__(self):
        return f"{self.title} ({self.department.code})"