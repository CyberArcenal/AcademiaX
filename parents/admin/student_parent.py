from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.parents import RelationshipType
from .parent import Parent

class StudentParent(TimestampedModel, UUIDModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='parents')
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='students')
    relationship = models.CharField(max_length=10, choices=RelationshipType.choices)
    is_primary_contact = models.BooleanField(default=False)
    can_pickup = models.BooleanField(default=True, help_text="Allowed to pick up student from school")
    receives_academic_updates = models.BooleanField(default=True)
    receives_disciplinary_updates = models.BooleanField(default=True)
    receives_payment_reminders = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [['student', 'parent']]
        ordering = ['student', '-is_primary_contact']

    def __str__(self):
        return f"{self.parent} - {self.student} ({self.get_relationship_display()})"