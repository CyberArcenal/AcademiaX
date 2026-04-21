from django.db import models
from common.base.models import TimestampedModel, UUIDModel

class ReportCard(TimestampedModel, UUIDModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='report_cards')
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE, related_name='report_cards')
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE, related_name='report_cards')
    gpa = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_units_earned = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    honors = models.CharField(max_length=100, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_url = models.URLField(blank=True)
    signed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['student', 'academic_year', 'term']]

    def __str__(self):
        return f"Report Card - {self.student} - {self.academic_year.name}"