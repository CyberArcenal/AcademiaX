from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from students.models import Guardian
from students.state_transition_services.guardian import GuardianStateTransitionService


@receiver(pre_save, sender=Guardian)
def guardian_pre_save(sender, instance, **kwargs):
    """Detect changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    if old_instance.is_primary != instance.is_primary:
        changes['is_primary'] = {'old': old_instance.is_primary, 'new': instance.is_primary}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Guardian)
def guardian_post_save(sender, instance, created, **kwargs):
    """After save, handle side effects."""
    if created:
        GuardianStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        GuardianStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes


@receiver(post_delete, sender=Guardian)
def guardian_post_delete(sender, instance, **kwargs):
    """When a guardian is deleted, if it was primary, reassign another."""
    GuardianStateTransitionService.handle_deletion(instance)