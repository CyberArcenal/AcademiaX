from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from assessments.models import Assessment
from assessments.state_transition_services.assessment import AssessmentStateTransitionService



@receiver(pre_save, sender=Assessment)
def assessment_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor is_published field
    if old_instance.is_published != instance.is_published:
        changes['is_published'] = {'old': old_instance.is_published, 'new': instance.is_published}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Assessment)
def assessment_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        AssessmentStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        AssessmentStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes