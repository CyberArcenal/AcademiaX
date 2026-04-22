from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from classes.models import AcademicYear, GradeLevel
from fees.models import Discount
from fees.services.discount import DiscountService
from fees.serializers.discount import (
    DiscountCreateSerializer,
    DiscountUpdateSerializer,
    DiscountDisplaySerializer,
)
from common.enums.fees import DiscountType, FeeCategory


class DiscountModelTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_percentage_discount(self):
        discount = Discount.objects.create(
            name="Early Bird",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal('10.00'),
            is_percentage=True,
            applicable_to='TUITION',
            academic_year=self.academic_year,
            valid_until=date(2025, 7, 31),
            is_active=True
        )
        self.assertEqual(discount.name, "Early Bird")
        self.assertEqual(discount.value, Decimal('10.00'))

    def test_create_fixed_discount(self):
        discount = Discount.objects.create(
            name="Scholarship",
            discount_type=DiscountType.FIXED,
            value=Decimal('5000.00'),
            is_percentage=False,
            applicable_to='ALL_FEES',
            is_active=True
        )
        self.assertEqual(discount.value, Decimal('5000.00'))

    def test_str_method(self):
        discount = Discount.objects.create(name="Test", discount_type=DiscountType.PERCENTAGE, value=Decimal('5.00'))
        self.assertEqual(str(discount), "Test (Percentage: 5.00)")


class DiscountServiceTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)

    def test_create_discount(self):
        discount = DiscountService.create_discount(
            name="Loyalty",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal('15.00'),
            is_percentage=True,
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            valid_until=date(2025, 12, 31)
        )
        self.assertEqual(discount.name, "Loyalty")

    def test_get_active_discounts(self):
        Discount.objects.create(name="Active1", is_active=True, valid_until=date.today() + timedelta(days=30))
        Discount.objects.create(name="Expired", is_active=True, valid_until=date.today() - timedelta(days=1))
        Discount.objects.create(name="Inactive", is_active=False, valid_until=date.today() + timedelta(days=30))
        active = DiscountService.get_active_discounts()
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().name, "Active1")

    def test_apply_discount_percentage(self):
        discount = Discount.objects.create(discount_type=DiscountType.PERCENTAGE, value=Decimal('10.00'), is_percentage=True)
        result = DiscountService.apply_discount(Decimal('1000.00'), discount)
        self.assertEqual(result, Decimal('100.00'))

    def test_apply_discount_fixed(self):
        discount = Discount.objects.create(discount_type=DiscountType.FIXED, value=Decimal('200.00'), is_percentage=False)
        result = DiscountService.apply_discount(Decimal('1000.00'), discount)
        self.assertEqual(result, Decimal('200.00'))


class DiscountSerializerTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYear.objects.create(name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31))

    def test_create_serializer_valid(self):
        data = {
            "name": "Summer Sale",
            "discount_type": DiscountType.PERCENTAGE,
            "value": "20.00",
            "is_percentage": True,
            "applicable_to": "TUITION",
            "academic_year_id": self.academic_year.id,
            "valid_until": "2025-08-31"
        }
        serializer = DiscountCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        discount = serializer.save()
        self.assertEqual(discount.name, "Summer Sale")

    def test_update_serializer(self):
        discount = Discount.objects.create(name="Old", discount_type=DiscountType.PERCENTAGE, value=Decimal('5.00'))
        data = {"name": "New", "value": "10.00"}
        serializer = DiscountUpdateSerializer(discount, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "New")

    def test_display_serializer(self):
        discount = Discount.objects.create(name="Display", discount_type=DiscountType.FIXED, value=Decimal('100.00'))
        serializer = DiscountDisplaySerializer(discount)
        self.assertEqual(serializer.data["name"], "Display")
        self.assertEqual(serializer.data["value"], "100.00")