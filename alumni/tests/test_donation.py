from django.test import TestCase
from datetime import date
from students.models import Student
from alumni.models import Alumni, Donation
from alumni.services.donation import DonationService
from alumni.serializers.donation import (
    DonationCreateSerializer,
    DonationUpdateSerializer,
    DonationDisplaySerializer,
)
from common.enums.alumni import DonationPurpose


class DonationModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date="2000-01-01",
            gender="M"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )

    def test_create_donation(self):
        donation = Donation.objects.create(
            alumni=self.alumni,
            amount=1000.00,
            date=date(2025, 1, 15),
            purpose=DonationPurpose.GENERAL,
            receipt_number="RCP-001"
        )
        self.assertEqual(donation.alumni, self.alumni)
        self.assertEqual(donation.amount, 1000.00)
        self.assertEqual(donation.purpose, DonationPurpose.GENERAL)

    def test_str_method(self):
        donation = Donation.objects.create(
            alumni=self.alumni,
            amount=500.00,
            date=date(2025, 1, 15)
        )
        expected = f"{self.alumni} - 500.00 on 2025-01-15"
        self.assertEqual(str(donation), expected)


class DonationServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria",
            last_name="Santos",
            birth_date="2001-02-02",
            gender="F"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )

    def test_create_donation(self):
        donation = DonationService.create_donation(
            alumni=self.alumni,
            amount=2500.00,
            date=date(2025, 1, 20),
            purpose=DonationPurpose.SCHOLARSHIP
        )
        self.assertEqual(donation.alumni, self.alumni)
        self.assertEqual(donation.amount, 2500.00)

    def test_get_donations_by_alumni(self):
        Donation.objects.create(alumni=self.alumni, amount=100, date=date(2025, 1, 1))
        Donation.objects.create(alumni=self.alumni, amount=200, date=date(2025, 2, 1))
        donations = DonationService.get_donations_by_alumni(self.alumni.id)
        self.assertEqual(donations.count(), 2)

    def test_get_total_donations_by_alumni(self):
        Donation.objects.create(alumni=self.alumni, amount=100, date=date(2025, 1, 1))
        Donation.objects.create(alumni=self.alumni, amount=200, date=date(2025, 2, 1))
        total = DonationService.get_total_donations_by_alumni(self.alumni.id)
        self.assertEqual(total, 300.00)

    def test_update_donation(self):
        donation = Donation.objects.create(alumni=self.alumni, amount=100, date=date(2025, 1, 1))
        updated = DonationService.update_donation(donation, {"amount": 150, "receipt_number": "NEW-RCP"})
        self.assertEqual(updated.amount, 150)
        self.assertEqual(updated.receipt_number, "NEW-RCP")

    def test_delete_donation(self):
        donation = Donation.objects.create(alumni=self.alumni, amount=100, date=date(2025, 1, 1))
        success = DonationService.delete_donation(donation)
        self.assertTrue(success)
        with self.assertRaises(Donation.DoesNotExist):
            Donation.objects.get(id=donation.id)


class DonationSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro",
            last_name="Penduko",
            birth_date="2002-03-03",
            gender="M"
        )
        self.alumni = Alumni.objects.create(
            student=self.student,
            graduation_year=2025
        )

    def test_create_serializer_valid(self):
        data = {
            "alumni_id": self.alumni.id,
            "amount": 5000.00,
            "date": "2025-01-15",
            "purpose": DonationPurpose.BUILDING
        }
        serializer = DonationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        donation = serializer.save()
        self.assertEqual(donation.alumni, self.alumni)

    def test_update_serializer(self):
        donation = Donation.objects.create(alumni=self.alumni, amount=100, date=date(2025, 1, 1))
        data = {"amount": 200, "remarks": "Updated remarks"}
        serializer = DonationUpdateSerializer(donation, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.amount, 200)
        self.assertEqual(updated.remarks, "Updated remarks")

    def test_display_serializer(self):
        donation = Donation.objects.create(alumni=self.alumni, amount=100, date=date(2025, 1, 1))
        serializer = DonationDisplaySerializer(donation)
        self.assertEqual(serializer.data["amount"], "100.00")
        self.assertEqual(serializer.data["alumni"]["id"], self.alumni.id)