from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.library import BorrowStatus
from library.models.copy import BookCopy


class BorrowTransaction(TimestampedModel, UUIDModel):
    copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='borrow_transactions')
    borrower = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='library_borrows')
    borrowed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='processed_borrows')
    borrow_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=BorrowStatus.choices, default=BorrowStatus.APPROVED)
    renewed_count = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-borrow_date']

    def __str__(self):
        return f"{self.borrower} borrowed {self.copy.book.title} (due {self.due_date})"