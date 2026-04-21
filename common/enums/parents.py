# common/enums/parents.py
from django.db import models

class RelationshipType(models.TextChoices):
    FATHER = 'FTH', 'Father'
    MOTHER = 'MTH', 'Mother'
    GUARDIAN = 'GRD', 'Legal Guardian'
    GRANDPARENT = 'GRP', 'Grandparent'
    SIBLING = 'SIB', 'Sibling'
    STEP_PARENT = 'STP', 'Step-parent'
    OTHER = 'OTH', 'Other'

class ParentStatus(models.TextChoices):
    ACTIVE = 'ACT', 'Active'
    INACTIVE = 'INA', 'Inactive'
    BLACKLISTED = 'BLK', 'Blacklisted'  # for non-compliance