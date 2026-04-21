from django.db import models

class GradeLevel(models.TextChoices):
    KINDERGARTEN = 'K', 'Kindergarten'
    GRADE_1 = 'G1', 'Grade 1'
    GRADE_2 = 'G2', 'Grade 2'
    GRADE_3 = 'G3', 'Grade 3'
    GRADE_4 = 'G4', 'Grade 4'
    GRADE_5 = 'G5', 'Grade 5'
    GRADE_6 = 'G6', 'Grade 6'
    GRADE_7 = 'G7', 'Grade 7'
    GRADE_8 = 'G8', 'Grade 8'
    GRADE_9 = 'G9', 'Grade 9'
    GRADE_10 = 'G10', 'Grade 10'
    GRADE_11 = 'G11', 'Grade 11'
    GRADE_12 = 'G12', 'Grade 12'

class Semester(models.TextChoices):
    FIRST = '1ST', 'First Semester'
    SECOND = '2ND', 'Second Semester'
    SUMMER = 'SUM', 'Summer'

class SubjectType(models.TextChoices):
    CORE = 'CORE', 'Core Subject'
    APPLIED = 'APP', 'Applied Subject'
    SPECIALIZED = 'SPEC', 'Specialized Subject'
    ELECTIVE = 'ELEC', 'Elective'

class CurriculumLevel(models.TextChoices):
    JUNIOR_HIGH = 'JHS', 'Junior High School (Grades 7-10)'
    SENIOR_HIGH = 'SHS', 'Senior High School (Grades 11-12)'
    COLLEGE = 'COL', 'College'  # optional