from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.grades import GradeStatus

class Grade(TimestampedModel, UUIDModel, SoftDeleteModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE, related_name='grades')
    enrollment = models.ForeignKey('enrollments.Enrollment', on_delete=models.CASCADE, related_name='grades')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='grades')
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE, related_name='grades')
    
    # Grade values
    raw_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    transmuted_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True)
    remarks = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=10, choices=GradeStatus.choices, default=GradeStatus.DRAFT)
    comments = models.TextField(blank=True)
    graded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [['student', 'subject', 'enrollment', 'term']]
        ordering = ['enrollment', 'subject__code']

    def __str__(self):
        return f"{self.student} - {self.subject.code} - {self.percentage}%"