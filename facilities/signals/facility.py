from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from facilities.models import Facility
from facilities.state_transition_service.facility import FacilityStateTransitionService


@receiver(pre_save, sender=Facility)
def facility_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor status (AVAILABLE, OCCUPIED, UNDER_MAINTENANCE, RESERVED, CLOSED)
    if old_instance.status != instance.status:
        changes['status'] = {'old': old_instance.status, 'new': instance.status}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Facility)
def facility_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        FacilityStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        FacilityStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes