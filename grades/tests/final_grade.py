from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.grades import GradeStatus

class FinalGrade(TimestampedModel, UUIDModel, SoftDeleteModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='final_grades')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE, related_name='final_grades')
    enrollment = models.ForeignKey('enrollments.Enrollment', on_delete=models.CASCADE, related_name='final_grades')
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE, related_name='final_grades')
    
    # Aggregated from quarter grades
    q1_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    q2_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    q3_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    q4_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    remarks = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=GradeStatus.choices, default=GradeStatus.DRAFT)

    class Meta:
        unique_together = [['student', 'subject', 'enrollment']]

    def __str__(self):
        return f"{self.student} - {self.subject.code} - Final: {self.final_grade}"