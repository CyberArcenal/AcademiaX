from django.test import TestCase
from datetime import date
from students.models import Student
from alumni.models import Alumni, PostGraduateEducation
from alumni.services.education import PostGraduateEducationService
from alumni.serializers.education import (
    PostGraduateEducationCreateSerializer,
    PostGraduateEducationUpdateSerializer,
    PostGraduateEducationDisplaySerializer,
)


class PostGraduateEducationModelTest(TestCase):
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

    def test_create_education(self):
        edu = PostGraduateEducation.objects.create(
            alumni=self.alumni,
            degree="Master of Science in Computer Science",
            institution="University of the Philippines",
            year_start=2025,
            year_end=2027,
            is_graduate=True
        )
        self.assertEqual(edu.alumni, self.alumni)
        self.assertEqual(edu.degree, "Master of Science in Computer Science")
        self.assertEqual(edu.year_start, 2025)
        self.assertTrue(edu.is_graduate)

    def test_str_method(self):
        edu = PostGraduateEducation.objects.create(
            alumni=self.alumni,
            degree="MBA",
            institution="Ateneo",
            year_start=2025
        )
        expected = f"{self.alumni} - MBA at Ateneo"
        self.assertEqual(str(edu), expected)


class PostGraduateEducationServiceTest(TestCase):
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

    def test_create_education(self):
        edu = PostGraduateEducationService.create_education(
            alumni=self.alumni,
            degree="PhD in Mathematics",
            institution="UST",
            year_start=2025,
            year_end=2029
        )
        self.assertEqual(edu.alumni, self.alumni)
        self.assertEqual(edu.degree, "PhD In Mathematics")
        self.assertEqual(edu.institution, "Ust")

    def test_get_educations_by_alumni(self):
        PostGraduateEducation.objects.create(alumni=self.alumni, degree="Master 1", institution="Univ A", year_start=2025)
        PostGraduateEducation.objects.create(alumni=self.alumni, degree="Master 2", institution="Univ B", year_start=2026)
        educations = PostGraduateEducationService.get_educations_by_alumni(self.alumni.id)
        self.assertEqual(educations.count(), 2)

    def test_update_education(self):
        edu = PostGraduateEducation.objects.create(
            alumni=self.alumni,
            degree="BS",
            institution="College",
            year_start=2025
        )
        updated = PostGraduateEducationService.update_education(
            edu,
            {"degree": "BS Computer Science", "year_end": 2029}
        )
        self.assertEqual(updated.degree, "Bs Computer Science")
        self.assertEqual(updated.year_end, 2029)

    def test_delete_education(self):
        edu = PostGraduateEducation.objects.create(alumni=self.alumni, degree="Test", institution="Univ", year_start=2025)
        success = PostGraduateEducationService.delete_education(edu)
        self.assertTrue(success)
        with self.assertRaises(PostGraduateEducation.DoesNotExist):
            PostGraduateEducation.objects.get(id=edu.id)


class PostGraduateEducationSerializerTest(TestCase):
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
            "degree": "Master in Business Administration",
            "institution": "DLSU",
            "year_start": 2025,
            "year_end": 2027
        }
        serializer = PostGraduateEducationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        edu = serializer.save()
        self.assertEqual(edu.alumni, self.alumni)

    def test_update_serializer(self):
        edu = PostGraduateEducation.objects.create(
            alumni=self.alumni,
            degree="Original Degree",
            institution="Original Univ",
            year_start=2025
        )
        data = {"degree": "Updated Degree", "is_graduate": False}
        serializer = PostGraduateEducationUpdateSerializer(edu, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.degree, "Updated Degree")
        self.assertFalse(updated.is_graduate)

    def test_display_serializer(self):
        edu = PostGraduateEducation.objects.create(
            alumni=self.alumni,
            degree="Diploma",
            institution="Institute",
            year_start=2025
        )
        serializer = PostGraduateEducationDisplaySerializer(edu)
        self.assertEqual(serializer.data["degree"], "Diploma")
        self.assertEqual(serializer.data["alumni"]["id"], self.alumni.id)