from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from library.models import BookCopy
from library.state_transition_services.copy import BookCopyStateTransitionService

@receiver(pre_save, sender=BookCopy)
def copy_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    if old_instance.status != instance.status:
        changes['status'] = {'old': old_instance.status, 'new': instance.status}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=BookCopy)
def copy_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        BookCopyStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        BookCopyStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes