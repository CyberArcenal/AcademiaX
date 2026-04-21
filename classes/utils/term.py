from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.classes import TermType
from .academic_year import AcademicYear

class Term(TimestampedModel, UUIDModel, SoftDeleteModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    term_type = models.CharField(max_length=10, choices=TermType.choices)
    term_number = models.PositiveSmallIntegerField(help_text="1 for first semester/quarter, 2 for second, etc.")
    name = models.CharField(max_length=50, help_text="e.g., First Semester, Quarter 1")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['academic_year', 'term_type', 'term_number']]
        ordering = ['academic_year', 'term_number']

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"