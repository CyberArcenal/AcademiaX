from django.db.models.signals import post_save
from django.dispatch import receiver
from alumni.models import Donation
from alumni.state_transition_service.donation import DonationStateTransitionService


@receiver(post_save, sender=Donation)
def donation_post_save(sender, instance, created, **kwargs):
    """After donation is created, handle side effects."""
    if created:
        DonationStateTransitionService.handle_creation(instance)