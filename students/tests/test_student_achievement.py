from django.test import TestCase
from datetime import date
from students.models import Student, StudentAchievement
from students.services.student_achievement import StudentAchievementService
from students.serializers.student_achievement import (
    StudentAchievementCreateSerializer,
    StudentAchievementUpdateSerializer,
    StudentAchievementDisplaySerializer,
)


class StudentAchievementModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Juan", last_name="Dela Cruz", birth_date="2010-01-01", gender="M"
        )

    def test_create_achievement(self):
        achievement = StudentAchievement.objects.create(
            student=self.student,
            title="Math Olympiad Winner",
            awarding_body="DepEd",
            date_awarded=date(2025, 3, 15),
            level="NATIONAL",
            description="First place in Math competition"
        )
        self.assertEqual(achievement.student, self.student)
        self.assertEqual(achievement.title, "Math Olympiad Winner")

    def test_str_method(self):
        achievement = StudentAchievement.objects.create(student=self.student, title="Best in Science")
        expected = f"{self.student} - Best in Science"
        self.assertEqual(str(achievement), expected)


class StudentAchievementServiceTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Maria", last_name="Santos", birth_date="2010-02-02", gender="F"
        )

    def test_create_achievement(self):
        achievement = StudentAchievementService.create_achievement(
            student=self.student,
            title="Art Contest Winner",
            awarding_body="School",
            date_awarded=date(2025, 4, 10),
            level="SCHOOL"
        )
        self.assertEqual(achievement.student, self.student)

    def test_get_achievements_by_student(self):
        StudentAchievement.objects.create(student=self.student, title="Award1", date_awarded=date(2025,1,1))
        StudentAchievement.objects.create(student=self.student, title="Award2", date_awarded=date(2025,2,1))
        achievements = StudentAchievementService.get_achievements_by_student(self.student.id)
        self.assertEqual(achievements.count(), 2)

    def test_update_achievement(self):
        achievement = StudentAchievement.objects.create(student=self.student, title="Old", date_awarded=date(2025,1,1))
        updated = StudentAchievementService.update_achievement(achievement, {"title": "New", "description": "Updated"})
        self.assertEqual(updated.title, "New")


class StudentAchievementSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="Pedro", last_name="Penduko", birth_date="2010-03-03", gender="M"
        )

    def test_create_serializer_valid(self):
        data = {
            "student_id": self.student.id,
            "title": "Leadership Award",
            "awarding_body": "Student Council",
            "date_awarded": "2025-05-20",
            "level": "SCHOOL"
        }
        serializer = StudentAchievementCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        achievement = serializer.save()
        self.assertEqual(achievement.student, self.student)

    def test_update_serializer(self):
        achievement = StudentAchievement.objects.create(student=self.student, title="Old", date_awarded=date(2025,1,1))
        data = {"title": "Updated", "certificate_url": "http://example.com/cert.pdf"}
        serializer = StudentAchievementUpdateSerializer(achievement, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "Updated")

    def test_display_serializer(self):
        achievement = StudentAchievement.objects.create(student=self.student, title="Display", date_awarded=date(2025,6,1))
        serializer = StudentAchievementDisplaySerializer(achievement)
        self.assertEqual(serializer.data["title"], "Display")
        self.assertEqual(serializer.data["student"]["id"], self.student.id)