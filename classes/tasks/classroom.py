from django.db import models
from common.base.models import TimestampedModel, UUIDModel, SoftDeleteModel
from common.enums.classes import RoomType

class Classroom(TimestampedModel, UUIDModel, SoftDeleteModel):
    room_number = models.CharField(max_length=20, unique=True)
    building = models.CharField(max_length=100, blank=True)
    floor = models.PositiveSmallIntegerField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=30)
    room_type = models.CharField(max_length=10, choices=RoomType.choices, default=RoomType.CLASSROOM)
    has_projector = models.BooleanField(default=False)
    has_aircon = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['building', 'floor', 'room_number']

    def __str__(self):
        return f"{self.room_number} ({self.get_room_type_display()})"