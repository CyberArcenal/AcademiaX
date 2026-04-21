from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from alumni.models import Alumni
from alumni.state_transition_service.alumni import AlumniStateTransitionService


@receiver(pre_save, sender=Alumni)
def alumni_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor is_active field
    if old_instance.is_active != instance.is_active:
        changes['is_active'] = {'old': old_instance.is_active, 'new': instance.is_active}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Alumni)
def alumni_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        AlumniStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        AlumniStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes