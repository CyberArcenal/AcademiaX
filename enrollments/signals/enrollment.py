from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from enrollments.models import Enrollment
from enrollments.state_transition_services.enrollment import EnrollmentStateTransitionService


@receiver(pre_save, sender=Enrollment)
def enrollment_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor status field (PENDING, ENROLLED, DROPPED, TRANSFERRED, GRADUATED, WITHDRAWN, ON_LEAVE, SUSPENDED)
    if old_instance.status != instance.status:
        changes['status'] = {'old': old_instance.status, 'new': instance.status}

    # Monitor payment_status (UNPAID, PARTIAL, PAID, SCHOLARSHIP)
    if old_instance.payment_status != instance.payment_status:
        changes['payment_status'] = {'old': old_instance.payment_status, 'new': instance.payment_status}

    # Monitor section changes
    if old_instance.section_id != instance.section_id:
        changes['section'] = {'old': old_instance.section_id, 'new': instance.section_id}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Enrollment)
def enrollment_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        EnrollmentStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        EnrollmentStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes