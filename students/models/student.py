from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.students import StudentStatus, Gender

class Student(TimestampedModel, UUIDModel, SoftDeleteModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=50, unique=True)
    lrn = models.CharField(max_length=20, blank=True, help_text="Learner Reference Number")
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    birth_date = models.DateField()
    birth_place = models.CharField(max_length=200, blank=True)
    nationality = models.CharField(max_length=100, default='Filipino')
    religion = models.CharField(max_length=100, blank=True)
    current_address = models.TextField()
    permanent_address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    personal_email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=StudentStatus.choices, default=StudentStatus.ACTIVE)
    enrollment_date = models.DateField(auto_now_add=True)
    profile_picture_url = models.URLField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.student_id} - {self.last_name}, {self.first_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name} {self.suffix}".strip()