from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from library.models import BorrowTransaction
from library.state_transition_services.borrow import BorrowTransactionStateTransitionService


@receiver(pre_save, sender=BorrowTransaction)
def borrow_pre_save(sender, instance, **kwargs):
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


@receiver(post_save, sender=BorrowTransaction)
def borrow_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        BorrowTransactionStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        BorrowTransactionStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes