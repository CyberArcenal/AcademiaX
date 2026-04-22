from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.fees import FeeCategory

class FeeStructure(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=200, help_text="e.g., Tuition Fee Grade 7, Laboratory Fee STEM")
    category = models.CharField(max_length=10, choices=FeeCategory.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE, related_name='fee_structures')
    grade_level = models.ForeignKey('classes.GradeLevel', on_delete=models.CASCADE, related_name='fee_structures', null=True, blank=True)
    academic_program = models.ForeignKey('academic.AcademicProgram', on_delete=models.CASCADE, related_name='fee_structures', null=True, blank=True)
    is_mandatory = models.BooleanField(default=True)
    is_per_semester = models.BooleanField(default=True, help_text="If false, annual fee")
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['academic_year', 'grade_level', 'category']

    def __str__(self):
        return f"{self.name} - {self.amount}"