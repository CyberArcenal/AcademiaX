from django.db import models
from common.base.models import TimestampedModel
from .student_attendance import StudentAttendance

class StudentAttendanceSummary(TimestampedModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendance_summaries')
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE)
    term = models.CharField(max_length=20)  # e.g., "First Quarter", "First Semester"
    total_present = models.PositiveIntegerField(default=0)
    total_absent = models.PositiveIntegerField(default=0)
    total_late = models.PositiveIntegerField(default=0)
    total_excused = models.PositiveIntegerField(default=0)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = [['student', 'academic_year', 'term']]

    def __str__(self):
        return f"{self.student} - {self.academic_year} - {self.term}"