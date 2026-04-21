from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from .student import Student

class StudentDocument(TimestampedModel, UUIDModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=[
        ('PSA_BIRTH', 'PSA Birth Certificate'),
        ('REPORT_CARD', 'Report Card (SF9)'),
        ('GOOD_MORAL', 'Good Moral Character'),
        ('TRANSFER', 'Transfer Credentials'),
        ('MEDICAL', 'Medical Certificate'),
        ('ID_PICTURE', '2x2 ID Picture'),
        ('OTHER', 'Other'),
    ])
    title = models.CharField(max_length=200)
    file_url = models.URLField()
    uploaded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.get_document_type_display()}"