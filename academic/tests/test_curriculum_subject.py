from django.test import TestCase
from django.core.exceptions import ValidationError
from academic.models import AcademicProgram, Curriculum, Subject, CurriculumSubject
from academic.services.curriculum_subject import CurriculumSubjectService
from academic.serializers.curriculum_subject import (
    CurriculumSubjectCreateSerializer,
    CurriculumSubjectUpdateSerializer,
    CurriculumSubjectDisplaySerializer,
)
from common.enums.academic import GradeLevel, Semester, SubjectType


class CurriculumSubjectModelTest(TestCase):
    def setUp(self):
        self.program = AcademicProgram.objects.create(
            code="STEM",
            name="STEM Program",
            level=GradeLevel.GRADE_11
        )
        self.curriculum = Curriculum.objects.create(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2025,
            is_current=True
        )
        self.subject = Subject.objects.create(
            code="MATH101",
            name="Algebra",
            units=3.0,
            subject_type=SubjectType.CORE
        )

    def test_create_curriculum_subject(self):
        cs = CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            year_level_order=1,
            semester=Semester.FIRST,
            sequence=1,
            is_required=True
        )
        self.assertEqual(cs.curriculum, self.curriculum)
        self.assertEqual(cs.subject, self.subject)
        self.assertEqual(cs.year_level_order, 1)
        self.assertEqual(cs.semester, Semester.FIRST)
        self.assertTrue(cs.is_required)

    def test_unique_together(self):
        CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            year_level_order=1
        )
        with self.assertRaises(Exception):
            CurriculumSubject.objects.create(
                curriculum=self.curriculum,
                subject=self.subject,
                year_level_order=1
            )

    def test_str_method(self):
        cs = CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            year_level_order=1
        )
        expected = f"{self.curriculum} - {self.subject.code}"
        self.assertEqual(str(cs), expected)


class CurriculumSubjectServiceTest(TestCase):
    def setUp(self):
        self.program = AcademicProgram.objects.create(
            code="ABM",
            name="ABM Program",
            level=GradeLevel.GRADE_11
        )
        self.curriculum = Curriculum.objects.create(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2025,
            is_current=True
        )
        self.subject1 = Subject.objects.create(code="MATH101", name="Algebra")
        self.subject2 = Subject.objects.create(code="MATH102", name="Geometry")

    def test_add_subject_to_curriculum(self):
        cs = CurriculumSubjectService.add_subject_to_curriculum(
            curriculum=self.curriculum,
            subject=self.subject1,
            year_level_order=1,
            semester=Semester.FIRST,
            sequence=1
        )
        self.assertEqual(cs.curriculum, self.curriculum)
        self.assertEqual(cs.subject, self.subject1)

    def test_get_subjects_by_curriculum(self):
        CurriculumSubject.objects.create(curriculum=self.curriculum, subject=self.subject1, year_level_order=1)
        CurriculumSubject.objects.create(curriculum=self.curriculum, subject=self.subject2, year_level_order=2)
        subjects = CurriculumSubjectService.get_subjects_by_curriculum(self.curriculum.id)
        self.assertEqual(subjects.count(), 2)

    def test_update_curriculum_subject(self):
        cs = CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject1,
            year_level_order=1,
            sequence=1
        )
        updated = CurriculumSubjectService.update_curriculum_subject(
            cs, {"year_level_order": 2, "sequence": 3, "is_required": False}
        )
        self.assertEqual(updated.year_level_order, 2)
        self.assertEqual(updated.sequence, 3)
        self.assertFalse(updated.is_required)

    def test_remove_subject_from_curriculum(self):
        cs = CurriculumSubject.objects.create(curriculum=self.curriculum, subject=self.subject1, year_level_order=1)
        success = CurriculumSubjectService.remove_subject_from_curriculum(cs)
        self.assertTrue(success)
        self.assertEqual(CurriculumSubject.objects.filter(id=cs.id).count(), 0)

    def test_reorder_sequence(self):
        cs1 = CurriculumSubject.objects.create(curriculum=self.curriculum, subject=self.subject1, year_level_order=1, sequence=1)
        cs2 = CurriculumSubject.objects.create(curriculum=self.curriculum, subject=self.subject2, year_level_order=1, sequence=2)
        success = CurriculumSubjectService.reorder_sequence(self.curriculum.id, [self.subject2.id, self.subject1.id])
        self.assertTrue(success)
        cs1.refresh_from_db()
        cs2.refresh_from_db()
        self.assertEqual(cs1.sequence, 2)
        self.assertEqual(cs2.sequence, 1)


class CurriculumSubjectSerializerTest(TestCase):
    def setUp(self):
        self.program = AcademicProgram.objects.create(
            code="HUMSS",
            name="HUMSS Program",
            level=GradeLevel.GRADE_11
        )
        self.curriculum = Curriculum.objects.create(
            academic_program=self.program,
            grade_level=GradeLevel.GRADE_11,
            year_effective=2025,
            is_current=True
        )
        self.subject = Subject.objects.create(code="ENG101", name="English")

    def test_create_serializer_valid(self):
        data = {
            "curriculum_id": self.curriculum.id,
            "subject_id": self.subject.id,
            "year_level_order": 1,
            "semester": Semester.FIRST,
            "sequence": 1,
            "is_required": True
        }
        serializer = CurriculumSubjectCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        cs = serializer.save()
        self.assertEqual(cs.curriculum, self.curriculum)
        self.assertEqual(cs.subject, self.subject)

    def test_update_serializer(self):
        cs = CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            year_level_order=1,
            sequence=1
        )
        data = {"year_level_order": 2, "sequence": 5, "is_required": False}
        serializer = CurriculumSubjectUpdateSerializer(cs, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.year_level_order, 2)
        self.assertEqual(updated.sequence, 5)
        self.assertFalse(updated.is_required)

    def test_display_serializer(self):
        cs = CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            year_level_order=1
        )
        serializer = CurriculumSubjectDisplaySerializer(cs)
        self.assertEqual(serializer.data["curriculum"]["id"], self.curriculum.id)
        self.assertEqual(serializer.data["subject"]["id"], self.subject.id)