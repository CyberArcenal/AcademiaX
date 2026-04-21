from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from students.models import Student
from students.state_transition_services.student import StudentStateTransitionService


@receiver(pre_save, sender=Student)
def student_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor status field (ACTIVE, INACTIVE, TRANSFERRED, GRADUATED, DROPPED, ON_LEAVE)
    if old_instance.status != instance.status:
        changes['status'] = {'old': old_instance.status, 'new': instance.status}

    # Monitor is_active (soft delete)
    if old_instance.is_active != instance.is_active:
        changes['is_active'] = {'old': old_instance.is_active, 'new': instance.is_active}

    # Monitor user association (optional)
    if old_instance.user_id != instance.user_id:
        changes['user'] = {'old': old_instance.user_id, 'new': instance.user_id}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Student)
def student_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        # For new student, maybe create default medical record or log
        StudentStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        StudentStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes