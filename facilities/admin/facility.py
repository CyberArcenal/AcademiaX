from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.facilities import FacilityType, FacilityStatus
from .building import Building

class Facility(TimestampedModel, UUIDModel, SoftDeleteModel):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='facilities')
    name = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=10, choices=FacilityType.choices)
    room_number = models.CharField(max_length=20, blank=True)
    floor = models.PositiveSmallIntegerField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=FacilityStatus.choices, default=FacilityStatus.AVAILABLE)
    description = models.TextField(blank=True)
    features = models.JSONField(default=list, blank=True, help_text="e.g., ['projector', 'aircon', 'wifi']")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['building', 'room_number']]
        ordering = ['building', 'floor', 'room_number']

    def __str__(self):
        return f"{self.building.name} - {self.name} ({self.get_facility_type_display()})"