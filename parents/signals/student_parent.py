from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from parents.models import StudentParent
from parents.state_transition_services.student_parent import StudentParentStateTransitionService


@receiver(post_save, sender=StudentParent)
def student_parent_post_save(sender, instance, created, **kwargs):
    """After relationship is created, handle effects."""
    if created:
        StudentParentStateTransitionService.handle_creation(instance)


@receiver(post_delete, sender=StudentParent)
def student_parent_post_delete(sender, instance, **kwargs):
    """When relationship is deleted, if it was primary, assign new primary."""
    StudentParentStateTransitionService.handle_deletion(instance)