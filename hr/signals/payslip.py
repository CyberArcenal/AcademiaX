from django.db.models.signals import post_save
from django.dispatch import receiver
from hr.models import Payslip
from hr.state_transition_services.payslip import PayslipStateTransitionService


@receiver(post_save, sender=Payslip)
def payslip_post_save(sender, instance, created, **kwargs):
    """After payslip is created or updated."""
    if created:
        PayslipStateTransitionService.handle_creation(instance)
    else:
        PayslipStateTransitionService.handle_update(instance)