from django.db import models
from django.conf import settings
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.teachers import TeacherStatus, TeacherType, HighestDegree

class Teacher(TimestampedModel, UUIDModel, SoftDeleteModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    teacher_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    birth_date = models.DateField()
    contact_number = models.CharField(max_length=20, blank=True)
    personal_email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=TeacherStatus.choices, default=TeacherStatus.ACTIVE)
    teacher_type = models.CharField(max_length=10, choices=TeacherType.choices, default=TeacherType.FULL_TIME)
    highest_degree = models.CharField(max_length=10, choices=HighestDegree.choices, blank=True)
    hire_date = models.DateField()
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    profile_picture_url = models.URLField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.teacher_id} - {self.last_name}, {self.first_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name} {self.suffix}".strip()