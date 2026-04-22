from django.test import TestCase
from datetime import date
from users.models import User
from teachers.models import Teacher, TeacherQualification
from teachers.services.teacher_qualification import TeacherQualificationService
from teachers.serializers.teacher_qualification import (
    TeacherQualificationCreateSerializer,
    TeacherQualificationUpdateSerializer,
    TeacherQualificationDisplaySerializer,
)


class TeacherQualificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher", email="t@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="John", last_name="Doe",
            birth_date=date(1980,1,1), gender="M", hire_date=date(2020,1,1)
        )

    def test_create_qualification(self):
        qual = TeacherQualification.objects.create(
            teacher=self.teacher,
            qualification_name="LET Passer",
            issuing_body="PRC",
            date_earned=date(2015, 3, 15),
            expiry_date=date(2025, 3, 15)
        )
        self.assertEqual(qual.teacher, self.teacher)
        self.assertEqual(qual.qualification_name, "LET Passer")

    def test_str_method(self):
        qual = TeacherQualification.objects.create(teacher=self.teacher, qualification_name="Master's Degree")
        expected = f"{self.teacher} - Master's Degree"
        self.assertEqual(str(qual), expected)


class TeacherQualificationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher2", email="t2@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Jane", last_name="Smith",
            birth_date=date(1985,1,1), gender="F", hire_date=date(2019,1,1)
        )

    def test_create_qualification(self):
        qual = TeacherQualificationService.create_qualification(
            teacher=self.teacher,
            qualification_name="PhD in Education",
            issuing_body="University",
            date_earned=date(2020, 5, 10),
            expiry_date=date(2030, 5, 10)
        )
        self.assertEqual(qual.teacher, self.teacher)

    def test_get_qualifications_by_teacher(self):
        TeacherQualification.objects.create(teacher=self.teacher, qualification_name="Cert1", date_earned=date(2010,1,1))
        TeacherQualification.objects.create(teacher=self.teacher, qualification_name="Cert2", date_earned=date(2015,1,1))
        quals = TeacherQualificationService.get_qualifications_by_teacher(self.teacher.id)
        self.assertEqual(quals.count(), 2)

    def test_get_active_qualifications(self):
        today = date.today()
        TeacherQualification.objects.create(teacher=self.teacher, qualification_name="Active", expiry_date=date(today.year + 1, 1, 1))
        TeacherQualification.objects.create(teacher=self.teacher, qualification_name="Expired", expiry_date=date(today.year - 1, 1, 1))
        active = TeacherQualificationService.get_active_qualifications(self.teacher.id)
        self.assertEqual(active.count(), 1)


class TeacherQualificationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher3", email="t3@example.com", password="test")
        self.teacher = Teacher.objects.create(
            user=self.user, first_name="Mark", last_name="Brown",
            birth_date=date(1975,1,1), gender="M", hire_date=date(2015,1,1)
        )

    def test_create_serializer_valid(self):
        data = {
            "teacher_id": self.teacher.id,
            "qualification_name": "Board Exam",
            "issuing_body": "PRC",
            "date_earned": "2018-06-01",
            "expiry_date": "2028-06-01"
        }
        serializer = TeacherQualificationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        qual = serializer.save()
        self.assertEqual(qual.teacher, self.teacher)

    def test_update_serializer(self):
        qual = TeacherQualification.objects.create(
            teacher=self.teacher, qualification_name="Old", date_earned=date(2010,1,1)
        )
        data = {"qualification_name": "New", "expiry_date": "2030-01-01"}
        serializer = TeacherQualificationUpdateSerializer(qual, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.qualification_name, "New")

    def test_display_serializer(self):
        qual = TeacherQualification.objects.create(
            teacher=self.teacher, qualification_name="Display", date_earned=date(2020,1,1)
        )
        serializer = TeacherQualificationDisplaySerializer(qual)
        self.assertEqual(serializer.data["qualification_name"], "Display")
        self.assertEqual(serializer.data["teacher"]["id"], self.teacher.id)