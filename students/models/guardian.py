from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.parents import RelationshipType
from .student import Student

class Guardian(TimestampedModel, UUIDModel, SoftDeleteModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardians')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    relationship = models.CharField(max_length=10, choices=RelationshipType.choices)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    lives_with_student = models.BooleanField(default=True)

    class Meta:
        ordering = ['student', '-is_primary']

    def __str__(self):
        return f"{self.last_name}, {self.first_name} - {self.student}"