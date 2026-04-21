from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.fees import DiscountType, FeeCategory

class Discount(TimestampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=200)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=8, decimal_places=2, help_text="Percentage or fixed amount")
    is_percentage = models.BooleanField(default=True)
    applicable_to = models.CharField(max_length=20, choices=[
        ('TUITION', 'Tuition Only'),
        ('ALL_FEES', 'All Fees'),
        ('SPECIFIC', 'Specific Fee Category'),
    ], default='TUITION')
    specific_category = models.CharField(max_length=10, choices=FeeCategory.choices, null=True, blank=True)
    academic_year = models.ForeignKey('classes.AcademicYear', on_delete=models.CASCADE, related_name='discounts', null=True, blank=True)
    grade_level = models.ForeignKey('classes.GradeLevel', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.discount_type}: {self.value})"