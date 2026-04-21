from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from library.models.copy import BookCopy

class Reservation(TimestampedModel, UUIDModel):
    copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='reservations')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='library_reservations')
    reservation_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['reservation_date']

    def __str__(self):
        return f"Reservation by {self.student} for {self.copy.book.title}"