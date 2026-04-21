from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from canteen.models import Order
from canteen.state_transition_services.order import OrderStateTransitionService


@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor status (PENDING, PREPARING, READY, COMPLETED, CANCELLED)
    if old_instance.status != instance.status:
        changes['status'] = {'old': old_instance.status, 'new': instance.status}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        OrderStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        OrderStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes