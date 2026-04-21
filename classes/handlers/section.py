from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from .grade_level import GradeLevel
from .academic_year import AcademicYear
from .classroom import Classroom
from .term import Term  # optional: if sections are term-specific

class Section(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=20, help_text="e.g., A, B, 1, St. Luke")
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='sections')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='sections')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='sections', null=True, blank=True,
                             help_text="If section is term-specific (e.g., summer class)")
    homeroom_teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homeroom_sections'
    )
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='sections')
    capacity = models.PositiveIntegerField(default=40)
    current_enrollment = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['name', 'grade_level', 'academic_year']]
        ordering = ['grade_level__order', 'name']

    def __str__(self):
        return f"{self.grade_level.name} - {self.name} ({self.academic_year.name})"