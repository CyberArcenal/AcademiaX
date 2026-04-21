from django.db import models
from common.base.models import TimestampedModel, UUIDModel
from common.enums.facilities import MaintenancePriority, MaintenanceStatus
from .facility import Facility
from .equipment import Equipment

class MaintenanceRequest(TimestampedModel, UUIDModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='maintenance_requests', null=True, blank=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_requests', null=True, blank=True)
    reported_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reported_maintenance')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=MaintenancePriority.choices, default=MaintenancePriority.MEDIUM)
    status = models.CharField(max_length=10, choices=MaintenanceStatus.choices, default=MaintenanceStatus.PENDING)
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_maintenance')
    scheduled_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"