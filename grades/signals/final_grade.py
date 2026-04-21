from django.db.models.signals import post_save
from django.dispatch import receiver
from grades.models import FinalGrade
from grades.state_transition_services.final_grade import FinalGradeStateTransitionService


@receiver(post_save, sender=FinalGrade)
def final_grade_post_save(sender, instance, created, **kwargs):
    """After save, handle effects."""
    if created:
        FinalGradeStateTransitionService.handle_creation(instance)
    else:
        FinalGradeStateTransitionService.handle_update(instance)