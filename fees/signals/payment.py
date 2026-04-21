from django.db.models.signals import post_save
from django.dispatch import receiver
from fees.models import Payment
from fees.state_transition_service.payment import PaymentStateTransitionService


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    """When a payment is created or updated, handle effects."""
    if created:
        PaymentStateTransitionService.handle_creation(instance)
    else:
        PaymentStateTransitionService.handle_update(instance)