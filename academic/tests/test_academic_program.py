from django.test import TestCase
from django.core.exceptions import ValidationError
from academic.models import AcademicProgram
from academic.services.academic_program import AcademicProgramService
from academic.serializers.academic_program import AcademicProgramCreateSerializer, AcademicProgramUpdateSerializer, AcademicProgramDisplaySerializer
from common.enums.academic import CurriculumLevel


class AcademicProgramModelTest(TestCase):
    def test_create_program_minimal(self):
        program = AcademicProgram.objects.create(
            code="STEM",
            name="Science, Technology, Engineering and Mathematics",
            level=CurriculumLevel.SENIOR_HIGH
        )
        self.assertEqual(program.code, "STEM")
        self.assertEqual(program.name, "Science, Technology, Engineering and Mathematics")
        self.assertTrue(program.is_active)

    def test_code_uppercase_auto(self):
        program = AcademicProgram.objects.create(
            code="stem",
            name="STEM Program",
            level=CurriculumLevel.SENIOR_HIGH
        )
        self.assertEqual(program.code, "STEM")

    def test_name_title_auto(self):
        program = AcademicProgram.objects.create(
            code="ABM",
            name="accountancy, business and management",
            level=CurriculumLevel.SENIOR_HIGH
        )
        self.assertEqual(program.name, "Accountancy, Business And Management")

    def test_unique_code_constraint(self):
        AcademicProgram.objects.create(code="GAS", name="General Academic Strand", level=CurriculumLevel.SENIOR_HIGH)
        with self.assertRaises(Exception):
            AcademicProgram.objects.create(code="GAS", name="Duplicate", level=CurriculumLevel.SENIOR_HIGH)

    def test_str_method(self):
        program = AcademicProgram.objects.create(code="HUMSS", name="Humanities and Social Sciences", level=CurriculumLevel.SENIOR_HIGH)
        self.assertEqual(str(program), "HUMSS - Humanities and Social Sciences")


class AcademicProgramServiceTest(TestCase):
    def test_create_program(self):
        program = AcademicProgramService.create_program(
            code="ICT",
            name="Information and Communications Technology",
            level=CurriculumLevel.SENIOR_HIGH
        )
        self.assertEqual(program.code, "ICT")
        self.assertEqual(program.name, "Information And Communications Technology")

    def test_get_program_by_id(self):
        created = AcademicProgram.objects.create(code="ARTS", name="Arts and Design", level=CurriculumLevel.SENIOR_HIGH)
        fetched = AcademicProgramService.get_program_by_id(created.id)
        self.assertEqual(fetched, created)

    def test_get_program_by_code(self):
        created = AcademicProgram.objects.create(code="SPORTS", name="Sports Track", level=CurriculumLevel.SENIOR_HIGH)
        fetched = AcademicProgramService.get_program_by_code("sports")
        self.assertEqual(fetched, created)

    def test_update_program(self):
        program = AcademicProgram.objects.create(code="OLD", name="Old Program", level=CurriculumLevel.SENIOR_HIGH)
        updated = AcademicProgramService.update_program(program, {"name": "New Program", "is_active": False})
        self.assertEqual(updated.name, "New Program")
        self.assertFalse(updated.is_active)

    def test_delete_program_soft(self):
        program = AcademicProgram.objects.create(code="DEL", name="To Delete", level=CurriculumLevel.SENIOR_HIGH)
        AcademicProgramService.delete_program(program, soft_delete=True)
        program.refresh_from_db()
        self.assertFalse(program.is_active)

    def test_delete_program_hard(self):
        program = AcademicProgram.objects.create(code="HARD", name="Hard Delete", level=CurriculumLevel.SENIOR_HIGH)
        AcademicProgramService.delete_program(program, soft_delete=False)
        with self.assertRaises(AcademicProgram.DoesNotExist):
            AcademicProgram.objects.get(id=program.id)

    def test_get_programs_by_level(self):
        AcademicProgram.objects.create(code="JHS1", name="JHS Program 1", level=CurriculumLevel.JUNIOR_HIGH)
        AcademicProgram.objects.create(code="JHS2", name="JHS Program 2", level=CurriculumLevel.JUNIOR_HIGH)
        AcademicProgram.objects.create(code="SHS1", name="SHS Program 1", level=CurriculumLevel.SENIOR_HIGH)
        jhs_programs = AcademicProgramService.get_programs_by_level(CurriculumLevel.JUNIOR_HIGH)
        self.assertEqual(jhs_programs.count(), 2)


class AcademicProgramSerializerTest(TestCase):
    def test_create_serializer_valid(self):
        data = {
            "code": "NEW",
            "name": "New Program",
            "level": CurriculumLevel.JUNIOR_HIGH
        }
        serializer = AcademicProgramCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        self.assertEqual(program.code, "NEW")

    def test_create_serializer_invalid_missing_code(self):
        data = {"name": "No Code", "level": CurriculumLevel.JUNIOR_HIGH}
        serializer = AcademicProgramCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_update_serializer(self):
        program = AcademicProgram.objects.create(code="OLD", name="Old Name", level=CurriculumLevel.JUNIOR_HIGH)
        data = {"name": "Updated Name", "is_active": False}
        serializer = AcademicProgramUpdateSerializer(program, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.name, "Updated Name")
        self.assertFalse(updated.is_active)

    def test_display_serializer(self):
        program = AcademicProgram.objects.create(code="DISPLAY", name="Display Test", level=CurriculumLevel.JUNIOR_HIGH)
        serializer = AcademicProgramDisplaySerializer(program)
        self.assertEqual(serializer.data["code"], "DISPLAY")
        self.assertEqual(serializer.data["name"], "Display Test")