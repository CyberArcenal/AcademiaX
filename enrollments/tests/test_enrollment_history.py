from django.test import TestCase
from datetime import date
from students.models import Student
from classes.models import AcademicYear, GradeLevel, Section
from users.models import User
from enrollments.models import Enrollment, EnrollmentHistory
from enrollments.services.enrollment_history import EnrollmentHistoryService
from enrollments.serializers.enrollment_history import (
    EnrollmentHistoryCreateSerializer,
    EnrollmentHistoryDisplaySerializer,
)
from common.enums.enrollment import EnrollmentStatus


class EnrollmentHistoryModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="A", grade_level=self.grade_level, academic_year=self.academic_year
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section,
            status=EnrollmentStatus.PENDING
        )

    def test_create_enrollment_history(self):
        history = EnrollmentHistory.objects.create(
            enrollment=self.enrollment,
            previous_status=None,
            new_status=EnrollmentStatus.PENDING,
            remarks="Initial enrollment"
        )
        self.assertEqual(history.enrollment, self.enrollment)
        self.assertEqual(history.new_status, EnrollmentStatus.PENDING)

    def test_str_method(self):
        history = EnrollmentHistory.objects.create(
            enrollment=self.enrollment,
            previous_status=EnrollmentStatus.PENDING,
            new_status=EnrollmentStatus.ENROLLED
        )
        expected = f"{self.enrollment} - Pending -> Enrolled"
        self.assertEqual(str(history), expected)


class EnrollmentHistoryServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="B", grade_level=self.grade_level, academic_year=self.academic_year
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section,
            status=EnrollmentStatus.PENDING
        )
        self.user = User.objects.create_user(username="reg", email="reg@example.com", password="test")

    def test_create_history(self):
        history = EnrollmentHistoryService.create_history(
            enrollment=self.enrollment,
            previous_status=EnrollmentStatus.PENDING,
            new_status=EnrollmentStatus.ENROLLED,
            remarks="Approved",
            changed_by=self.user
        )
        self.assertEqual(history.enrollment, self.enrollment)
        self.assertEqual(history.new_status, EnrollmentStatus.ENROLLED)

    def test_get_history_by_enrollment(self):
        EnrollmentHistory.objects.create(enrollment=self.enrollment, previous_status=None, new_status=EnrollmentStatus.PENDING)
        EnrollmentHistory.objects.create(enrollment=self.enrollment, previous_status=EnrollmentStatus.PENDING, new_status=EnrollmentStatus.ENROLLED)
        history_list = EnrollmentHistoryService.get_history_by_enrollment(self.enrollment.id)
        self.assertEqual(history_list.count(), 2)


class EnrollmentHistorySerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025,6,1), end_date=date(2026,5,31)
        )
        self.grade_level = GradeLevel.objects.create(level="G7", name="Grade 7", order=7)
        self.section = Section.objects.create(
            name="C", grade_level=self.grade_level, academic_year=self.academic_year
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, academic_year=self.academic_year,
            grade_level=self.grade_level, section=self.section,
            status=EnrollmentStatus.PENDING
        )

    def test_create_serializer_valid(self):
        data = {
            "enrollment_id": self.enrollment.id,
            "previous_status": EnrollmentStatus.PENDING,
            "new_status": EnrollmentStatus.ENROLLED,
            "remarks": "Approved"
        }
        serializer = EnrollmentHistoryCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        history = serializer.save()
        self.assertEqual(history.enrollment, self.enrollment)

    def test_display_serializer(self):
        history = EnrollmentHistory.objects.create(
            enrollment=self.enrollment, previous_status=None, new_status=EnrollmentStatus.PENDING
        )
        serializer = EnrollmentHistoryDisplaySerializer(history)
        self.assertEqual(serializer.data["enrollment"]["id"], self.enrollment.id)
        self.assertEqual(serializer.data["new_status"], EnrollmentStatus.PENDING)