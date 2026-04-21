from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.academic import GradeLevel, Semester
from .subject import Subject
from .academic_program import AcademicProgram

class Curriculum(TimestampedModel, UUIDModel, SoftDeleteModel):
    """Curriculum is a collection of subjects for a specific grade level and program."""
    academic_program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, related_name='curricula')
    grade_level = models.CharField(max_length=10, choices=GradeLevel.choices)
    year_effective = models.IntegerField(help_text="School year when this curriculum takes effect, e.g., 2025")
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = [['academic_program', 'grade_level', 'year_effective']]
        ordering = ['academic_program', 'grade_level', '-year_effective']

    def __str__(self):
        return f"{self.academic_program.name} - {self.get_grade_level_display()} ({self.year_effective})"

class CurriculumSubject(TimestampedModel, UUIDModel):
    """Which subjects belong to a curriculum, and their sequence/semester."""
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='curriculum_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='curriculum_subjects')
    semester = models.CharField(max_length=5, choices=Semester.choices, blank=True, null=True)
    year_level_order = models.PositiveSmallIntegerField(help_text="1 for 1st year, 2 for 2nd year, etc.")
    is_required = models.BooleanField(default=True)
    sequence = models.PositiveSmallIntegerField(help_text="Order within semester/year")

    class Meta:
        unique_together = [['curriculum', 'subject']]
        ordering = ['curriculum', 'year_level_order', 'semester', 'sequence']

    def __str__(self):
        return f"{self.curriculum} - {self.subject.code}"