from django.test import TestCase
from students.models import Student, MedicalRecord
from students.services.medical_record import MedicalRecordService
from students.serializers.medical_record import (
    MedicalRecordCreateSerializer,
    MedicalRecordUpdateSerializer,
    MedicalRecordDisplaySerializer,
)
from common.enums.students import BloodType


class MedicalRecordModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )

    def test_create_medical_record(self):
        record = MedicalRecord.objects.create(
            student=self.student,
            blood_type=BloodType.O_POS,
            allergies="Pollen",
            medical_conditions="Asthma",
            emergency_contact_name="Maria Dela Cruz",
            emergency_contact_number="09123456789"
        )
        self.assertEqual(record.student, self.student)
        self.assertEqual(record.blood_type, BloodType.O_POS)

    def test_str_method(self):
        record = MedicalRecord.objects.create(student=self.student)
        expected = f"Medical Record - {self.student}"
        self.assertEqual(str(record), expected)


class MedicalRecordServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )

    def test_create_or_update_record(self):
        record = MedicalRecordService.create_or_update_record(
            student=self.student,
            blood_type=BloodType.A_POS,
            allergies="None",
            medical_conditions="None"
        )
        self.assertEqual(record.student, self.student)
        self.assertEqual(record.blood_type, BloodType.A_POS)

    def test_get_medical_record_by_student(self):
        MedicalRecord.objects.create(student=self.student, blood_type=BloodType.B_POS)
        fetched = MedicalRecordService.get_medical_record_by_student(self.student.id)
        self.assertIsNotNone(fetched)


class MedicalRecordSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "blood_type": BloodType.AB_POS,
            "allergies": "Dust",
            "emergency_contact_name": "Juana Penduko",
            "emergency_contact_number": "09123456789"
        }
        serializer = MedicalRecordCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        record = serializer.save()
        self.assertEqual(record.student, self.student)

    def test_update_serializer(self):
        record = MedicalRecord.objects.create(student=self.student, blood_type=BloodType.O_NEG)
        data = {"blood_type": BloodType.A_NEG, "notes": "Updated notes"}
        serializer = MedicalRecordUpdateSerializer(record, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.blood_type, BloodType.A_NEG)

    def test_display_serializer(self):
        record = MedicalRecord.objects.create(student=self.student, blood_type=BloodType.AB_NEG)
        serializer = MedicalRecordDisplaySerializer(record)
        self.assertEqual(serializer.data["blood_type"], BloodType.AB_NEG)
        self.assertEqual(serializer.data["student"]["id"], self.student.id)