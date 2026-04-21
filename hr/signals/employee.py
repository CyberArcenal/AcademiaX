from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from hr.models import Employee
from hr.state_transition_services.employee import EmployeeStateTransitionService


@receiver(pre_save, sender=Employee)
def employee_pre_save(sender, instance, **kwargs):
    """Detect state changes before saving."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    changes = {}

    # Monitor status (ACTIVE, RESIGNED, TERMINATED, RETIRED, ON_LEAVE, SUSPENDED)
    if old_instance.status != instance.status:
        changes['status'] = {'old': old_instance.status, 'new': instance.status}

    # Monitor is_active (soft delete)
    if old_instance.is_active != instance.is_active:
        changes['is_active'] = {'old': old_instance.is_active, 'new': instance.is_active}

    if changes:
        instance._state_transition_changes = changes


@receiver(post_save, sender=Employee)
def employee_post_save(sender, instance, created, **kwargs):
    """After save, handle state transitions."""
    if created:
        EmployeeStateTransitionService.handle_creation(instance)
        return

    if hasattr(instance, '_state_transition_changes'):
        changes = instance._state_transition_changes
        EmployeeStateTransitionService.handle_changes(instance, changes)
        del instance._state_transition_changes