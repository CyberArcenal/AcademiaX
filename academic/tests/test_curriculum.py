from django.test import TestCase
from django.core.exceptions import ValidationError
from academic.models import AcademicProgram, Curriculum
from academic.services.curriculum import CurriculumService
from academic.serializers.curriculum import CurriculumCreateSerializer, CurriculumUpdateSerializer, CurriculumDisplaySerializer
from common.enums.academic import GradeLevel


class CurriculumModelTest(TestCase):
    def setUp(self):
        self.program = AcademicProgram.objects.create(
            code="STEM",
            name="STEM Program",
            level=GradeLevel.GRADE_11
        )

    def test_create_curriculum(self):
        curriculum = Curriculum.objects.create(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2025,
            is_current=True
        )
        self.assertEqual(curriculum.academic_program, self.program)
        self.assertEqual(curriculum.grade_level, GradeLevel.GRADE_11)
        self.assertEqual(curriculum.year_effective, 2025)
        self.assertTrue(curriculum.is_current)

    def test_unique_together(self):
        Curriculum.objects.create(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2025
        )
        with self.assertRaises(Exception):
            Curriculum.objects.create(
                academic_program=self.program,
                grade_level=GradeLevel.GRADE_11,
                year_effective=2025
            )

    def test_str_method(self):
        curriculum = Curriculum.objects.create(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2025
        )
        expected = f"{self.program.name} - Grade 11 (2025)"
        self.assertEqual(str(curriculum), expected)


class CurriculumServiceTest(TestCase):
    def setUp(self):
        self.program = AcademicProgram.objects.create(
            code="ABM",
            name="ABM Program",
            level=GradeLevel.GRADE_11
        )

    def test_create_curriculum(self):
        curriculum = CurriculumService.create_curriculum(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2025,
            is_current=True
        )
        self.assertEqual(curriculum.academic_program, self.program)
        self.assertTrue(curriculum.is_current)

    def test_set_current_unset_previous(self):
        c1 = CurriculumService.create_curriculum(self.program, GradeLevel.GRADE_11, 2024, is_current=True)
        c2 = CurriculumService.create_curriculum(self.program, GradeLevel.GRADE_11, 2025, is_current=True)
        c1.refresh_from_db()
        self.assertFalse(c1.is_current)
        self.assertTrue(c2.is_current)

    def test_get_current_curriculum(self):
        Curriculum.objects.create(academic_program=self.program, grade_level=GradeLevel.GRADE_11, year_effective=2024, is_current=False)
        current = Curriculum.objects.create(academic_program=self.program, grade_level=GradeLevel.GRADE_11, year_effective=2025, is_current=True)
        fetched = CurriculumService.get_current_curriculum(self.program.id, GradeLevel.GRADE_11)
        self.assertEqual(fetched, current)

    def test_update_curriculum_set_current(self):
        c1 = Curriculum.objects.create(academic_program=self.program, grade_level=GradeLevel.GRADE_11, year_effective=2024, is_current=True)
        c2 = Curriculum.objects.create(academic_program=self.program, grade_level=GradeLevel.GRADE_11, year_effective=2025, is_current=False)
        updated = CurriculumService.update_curriculum(c2, {"is_current": True})
        c1.refresh_from_db()
        self.assertFalse(c1.is_current)
        self.assertTrue(updated.is_current)


class CurriculumSerializerTest(TestCase):
    def setUp(self):
        self.program = AcademicProgram.objects.create(
            code="GAS",
            name="GAS Program",
            level=GradeLevel.GRADE_11
        )

    def test_create_serializer_valid(self):
        data = {
            "academic_program_id": self.program.id,
            "grade_level": GradeLevel.GRADE_11,
            "year_effective": 2025,
            "is_current": True
        }
        serializer = CurriculumCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        curriculum = serializer.save()
        self.assertEqual(curriculum.academic_program, self.program)

    def test_update_serializer(self):
        curriculum = Curriculum.objects.create(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2024,
            is_current=False
        )
        data = {"year_effective": 2026, "is_current": True}
        serializer = CurriculumUpdateSerializer(curriculum, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.year_effective, 2026)
        self.assertTrue(updated.is_current)