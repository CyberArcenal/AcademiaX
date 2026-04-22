from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from fees.models import FeeAssessment
from fees.state_transition_services.fee_assessment import FeeAssessmentStateTransitionService



@receiver(pre_save, sender=FeeAssessment)
def fee_assessment_pre_save(sender, instance, **kwargs):
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


@receiver(post_save, sender=FeeAssessment)
def fee_assessment_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        FeeAssessmentStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        FeeAssessmentStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes