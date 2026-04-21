from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr"
    def ready(self):
        import hr.signals.employee
        import hr.signals.leave
        import hr.signals.payslip