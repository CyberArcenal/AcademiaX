from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.academic import CurriculumLevel

class AcademicProgram(TimestampedModel, UUIDModel, SoftDeleteModel):
    code = models.CharField(max_length=20, unique=True)  # e.g., STEM, ABM, BSCS
    name = models.CharField(max_length=200)              # e.g., Science, Technology, Engineering and Mathematics
    level = models.CharField(max_length=10, choices=CurriculumLevel.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['level', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"