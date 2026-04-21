from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from communication.models import Notification
from communication.state_transition_services.notification import NotificationStateTransitionService



@receiver(pre_save, sender=Notification)
def notification_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor is_read field
    if old_instance.is_read != instance.is_read:
        changes['is_read'] = {'old': old_instance.is_read, 'new': instance.is_read}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        NotificationStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        NotificationStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes