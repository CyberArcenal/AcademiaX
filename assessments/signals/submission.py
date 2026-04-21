from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from assessments.models import Submission
from assessments.state_transition_service.submission import SubmissionStateTransitionService


@receiver(pre_save, sender=Submission)
def submission_pre_save(sender, instance, **kwargs):
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


@receiver(post_save, sender=Submission)
def submission_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        SubmissionStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        SubmissionStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes