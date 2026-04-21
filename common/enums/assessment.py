# common/enums/assessment.py
from django.db import models

class AssessmentType(models.TextChoices):
    QUIZ = 'QZ', 'Quiz'
    EXAM = 'EX', 'Exam'
    ASSIGNMENT = 'AS', 'Assignment'
    PROJECT = 'PR', 'Project'
    RECITATION = 'RC', 'Recitation'
    PRACTICAL = 'PT', 'Practical Exam'

class QuestionType(models.TextChoices):
    MULTIPLE_CHOICE = 'MC', 'Multiple Choice'
    TRUE_FALSE = 'TF', 'True or False'
    IDENTIFICATION = 'ID', 'Identification'
    ESSAY = 'ES', 'Essay'
    FILL_BLANK = 'FB', 'Fill in the Blank'
    MATCHING = 'MT', 'Matching Type'

class SubmissionStatus(models.TextChoices):
    DRAFT = 'DR', 'Draft'
    SUBMITTED = 'SB', 'Submitted'
    LATE = 'LT', 'Late'
    MISSING = 'MS', 'Missing'
    RETURNED = 'RT', 'Returned'

class GradingStatus(models.TextChoices):
    NOT_STARTED = 'NS', 'Not Started'
    IN_PROGRESS = 'IP', 'In Progress'
    GRADED = 'GD', 'Graded'
    PENDING_REVIEW = 'PR', 'Pending Review'