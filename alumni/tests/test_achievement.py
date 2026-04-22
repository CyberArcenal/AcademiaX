from django.test import TestCase
from datetime import date
from students.models import Student
from alumni.models import Alumni, AlumniAchievement
from alumni.services.achievement import AlumniAchievementService
from alumni.serializers.achievement import (
    AlumniAchievementCreateSerializer,
    AlumniAchievementUpdateSerializer,
    AlumniAchievementDisplaySerializer,
)


class AlumniAchievementModelTest(TestCase):
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

    def test_create_achievement(self):
        achievement = AlumniAchievement.objects.create(
            alumni=self.alumni,
            title="Top 10 Under 40",
            awarding_body="Forbes",
            date_received=date(2025, 1, 15)
        )
        self.assertEqual(achievement.alumni, self.alumni)
        self.assertEqual(achievement.title, "Top 10 Under 40")
        self.assertEqual(achievement.awarding_body, "Forbes")

    def test_str_method(self):
        achievement = AlumniAchievement.objects.create(
            alumni=self.alumni,
            title="Best Thesis Award",
            awarding_body="University",
            date_received=date(2025, 1, 1)
        )
        expected = f"{self.alumni} - Best Thesis Award"
        self.assertEqual(str(achievement), expected)


class AlumniAchievementServiceTest(TestCase):
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

    def test_create_achievement(self):
        achievement = AlumniAchievementService.create_achievement(
            alumni=self.alumni,
            title="Innovation Award",
            awarding_body="Tech Council",
            date_received=date(2025, 2, 10)
        )
        self.assertEqual(achievement.alumni, self.alumni)
        self.assertEqual(achievement.title, "Innovation Award")

    def test_get_achievements_by_alumni(self):
        AlumniAchievement.objects.create(alumni=self.alumni, title="Award 1", awarding_body="Org A", date_received=date(2025, 1, 1))
        AlumniAchievement.objects.create(alumni=self.alumni, title="Award 2", awarding_body="Org B", date_received=date(2025, 2, 1))
        achievements = AlumniAchievementService.get_achievements_by_alumni(self.alumni.id)
        self.assertEqual(achievements.count(), 2)

    def test_update_achievement(self):
        achievement = AlumniAchievement.objects.create(
            alumni=self.alumni,
            title="Original",
            awarding_body="Body",
            date_received=date(2025, 1, 1)
        )
        updated = AlumniAchievementService.update_achievement(
            achievement,
            {"title": "Updated Title", "description": "New description"}
        )
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.description, "New description")

    def test_delete_achievement(self):
        achievement = AlumniAchievement.objects.create(
            alumni=self.alumni,
            title="To Delete",
            awarding_body="Org",
            date_received=date(2025, 1, 1)
        )
        success = AlumniAchievementService.delete_achievement(achievement)
        self.assertTrue(success)
        with self.assertRaises(AlumniAchievement.DoesNotExist):
            AlumniAchievement.objects.get(id=achievement.id)


class AlumniAchievementSerializerTest(TestCase):
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
            "title": "Leadership Award",
            "awarding_body": "Student Council",
            "date_received": "2025-01-15"
        }
        serializer = AlumniAchievementCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        achievement = serializer.save()
        self.assertEqual(achievement.alumni, self.alumni)

    def test_update_serializer(self):
        achievement = AlumniAchievement.objects.create(
            alumni=self.alumni,
            title="Original",
            awarding_body="Body",
            date_received=date(2025, 1, 1)
        )
        data = {"title": "New Title", "certificate_url": "http://example.com/cert.pdf"}
        serializer = AlumniAchievementUpdateSerializer(achievement, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.certificate_url, "http://example.com/cert.pdf")

    def test_display_serializer(self):
        achievement = AlumniAchievement.objects.create(
            alumni=self.alumni,
            title="Display Test",
            awarding_body="Test Org",
            date_received=date(2025, 1, 1)
        )
        serializer = AlumniAchievementDisplaySerializer(achievement)
        self.assertEqual(serializer.data["title"], "Display Test")
        self.assertEqual(serializer.data["alumni"]["id"], self.alumni.id)