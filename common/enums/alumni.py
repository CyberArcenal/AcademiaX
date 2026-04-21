from django.db import models

class EmploymentType(models.TextChoices):
    FULL_TIME = 'FT', 'Full-time'
    PART_TIME = 'PT', 'Part-time'
    SELF_EMPLOYED = 'SE', 'Self-employed'
    CONTRACT = 'CT', 'Contractual'
    INTERNSHIP = 'IN', 'Internship'
    UNEMPLOYED = 'UN', 'Unemployed'

class DonationPurpose(models.TextChoices):
    SCHOLARSHIP = 'SCH', 'Scholarship Fund'
    BUILDING = 'BLD', 'Building Fund'
    GENERAL = 'GEN', 'General Fund'
    EVENT = 'EVT', 'Event Sponsorship'
    EQUIPMENT = 'EQP', 'Equipment'

class RSVPStatus(models.TextChoices):
    GOING = 'GO', 'Going'
    NOT_GOING = 'NG', 'Not Going'
    MAYBE = 'MB', 'Maybe'
    NO_RESPONSE = 'NR', 'No Response'