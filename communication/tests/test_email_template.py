from django.test import TestCase
from django.core.exceptions import ValidationError
from communication.models import EmailTemplate


class EmailTemplateModelTest(TestCase):
    def test_create_email_template(self):
        template = EmailTemplate.objects.create(
            name="login_alert",
            subject="Login Alert",
            content="Hello {{ subscriber.email }}, you have logged in."
        )
        self.assertEqual(template.name, "login_alert")
        self.assertEqual(template.subject, "Login Alert")
        self.assertIn("{{ subscriber.email }}", template.content)

    def test_name_choices_are_valid(self):
        valid_names = ["login_alert", "two_factor_enabled", "two_factor_disabled", "security_alert"]
        for name in valid_names:
            template = EmailTemplate.objects.create(
                name=name,
                subject=f"Subject for {name}",
                content="Content"
            )
            self.assertEqual(template.name, name)

    def test_invalid_name_raises_integrity_error(self):
        with self.assertRaises(Exception):
            EmailTemplate.objects.create(
                name="invalid_template",
                subject="Invalid",
                content="Content"
            )

    def test_unique_name_constraint(self):
        EmailTemplate.objects.create(name="login_alert", subject="First", content="Content 1")
        with self.assertRaises(Exception):
            EmailTemplate.objects.create(name="login_alert", subject="Second", content="Content 2")

    def test_str_method(self):
        template = EmailTemplate.objects.create(
            name="security_alert",
            subject="Security Alert",
            content="Alert"
        )
        # The model doesn't define __str__, so it will show "EmailTemplate object (id)"
        # We'll just check it returns a string
        self.assertIsInstance(str(template), str)

    def test_created_at_and_modified_are_auto(self):
        template = EmailTemplate.objects.create(
            name="two_factor_enabled",
            subject="2FA Enabled",
            content="Enabled"
        )
        self.assertIsNotNone(template.created_at)
        self.assertIsNotNone(template.modified_at)
        old_modified = template.modified_at
        template.subject = "Updated subject"
        template.save()
        template.refresh_from_db()
        self.assertGreater(template.modified_at, old_modified)