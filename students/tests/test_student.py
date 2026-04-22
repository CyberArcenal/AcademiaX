from django.test import TestCase
from datetime import date
from users.models import User
from students.models import Student
from students.services.student import StudentService
from students.serializers.student import (
    StudentCreateSerializer,
    StudentUpdateSerializer,
    StudentDisplaySerializer,
)
from common.enums.students import StudentStatus, Gender


class StudentModelTest(TestCase):
    def test_create_student(self):
        student = Student.objects.create(
            first_name="Juan",
            last_name="Dela Cruz",
            birth_date=date(2010, 1, 1),
            gender=Gender.MALE,
            student_id="2025-000001",
            lrn="123456789012"
        )
        self.assertEqual(student.first_name, "Juan")
        self.assertEqual(student.student_id, "2025-000001")

    def test_get_full_name(self):
        student = Student.objects.create(
            first_name="Maria",
            middle_name="Santos",
            last_name="Dela Cruz",
            suffix="Jr."
        )
        self.assertEqual(student.get_full_name(), "Maria Santos Dela Cruz Jr.")

    def test_str_method(self):
        student = Student.objects.create(first_name="Pedro", last_name="Penduko", student_id="2025-001")
        self.assertEqual(str(student), "2025-001 - Penduko, Pedro")


class StudentServiceTest(TestCase):
    def test_generate_student_id(self):
        student_id = StudentService.generate_student_id()
        self.assertTrue(student_id.startswith(str(date.today().year)))
        self.assertEqual(len(student_id), 11)  # YYYY-XXXXXX

    def test_create_student(self):
        student = StudentService.create_student(
            first_name="Jose",
            last_name="Rizal",
            birth_date=date(1861, 6, 19),
            gender=Gender.MALE
        )
        self.assertIsNotNone(student.student_id)
        self.assertEqual(student.status, StudentStatus.ACTIVE)

    def test_get_student_by_student_id(self):
        created = Student.objects.create(first_name="Test", last_name="User", student_id="2025-999999")
        fetched = StudentService.get_student_by_student_id("2025-999999")
        self.assertEqual(fetched, created)

    def test_update_status(self):
        student = Student.objects.create(first_name="ToUpdate", last_name="Status", status=StudentStatus.ACTIVE)
        updated = StudentService.update_status(student, StudentStatus.GRADUATED)
        self.assertEqual(updated.status, StudentStatus.GRADUATED)

    def test_search_students(self):
        Student.objects.create(first_name="Juan", last_name="Dela Cruz", student_id="2025-001")
        Student.objects.create(first_name="Maria", last_name="Santos", student_id="2025-002")
        results = StudentService.search_students("Juan")
        self.assertEqual(results.count(), 1)


class StudentSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "first_name": "Andres",
            "last_name": "Bonifacio",
            "birth_date": "1863-11-30",
            "gender": Gender.MALE,
            "lrn": "987654321098"
        }
        serializer = StudentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        student = serializer.save()
        self.assertEqual(student.first_name, "Andres")

    def test_update_serializer(self):
        student = Student.objects.create(first_name="Old", last_name="Name", birth_date=date(2000,1,1), gender=Gender.MALE)
        data = {"first_name": "New", "contact_number": "09123456789"}
        serializer = StudentUpdateSerializer(student, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.first_name, "New")

    def test_display_serializer(self):
        student = Student.objects.create(first_name="Display", last_name="Test", birth_date=date(2000,1,1), gender=Gender.MALE)
        serializer = StudentDisplaySerializer(student)
        self.assertEqual(serializer.data["first_name"], "Display")
        self.assertEqual(serializer.data["full_name"], "Display  Test")