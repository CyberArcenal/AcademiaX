from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any

from ..models.report_template import ReportTemplate
from ...users.models import User
from ...common.enums.reports import ReportType

class ReportTemplateService:
    """Service for ReportTemplate model operations"""

    @staticmethod
    def create_template(
        name: str,
        report_type: str,
        template_file,
        description: str = "",
        is_default: bool = False,
        is_active: bool = True,
        created_by: Optional[User] = None
    ) -> ReportTemplate:
        try:
            with transaction.atomic():
                # If setting is_default, unset previous default for this report type
                if is_default:
                    ReportTemplate.objects.filter(report_type=report_type, is_default=True).update(is_default=False)

                template = ReportTemplate(
                    name=name,
                    report_type=report_type,
                    template_file=template_file,
                    description=description,
                    is_default=is_default,
                    is_active=is_active,
                    created_by=created_by
                )
                template.full_clean()
                template.save()
                return template
        except ValidationError as e:
            raise

    @staticmethod
    def get_template_by_id(template_id: int) -> Optional[ReportTemplate]:
        try:
            return ReportTemplate.objects.get(id=template_id)
        except ReportTemplate.DoesNotExist:
            return None

    @staticmethod
    def get_templates_by_type(report_type: str, active_only: bool = True) -> List[ReportTemplate]:
        queryset = ReportTemplate.objects.filter(report_type=report_type)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    @staticmethod
    def get_default_template(report_type: str) -> Optional[ReportTemplate]:
        try:
            return ReportTemplate.objects.get(report_type=report_type, is_default=True, is_active=True)
        except ReportTemplate.DoesNotExist:
            return None

    @staticmethod
    def update_template(template: ReportTemplate, update_data: Dict[str, Any]) -> ReportTemplate:
        try:
            with transaction.atomic():
                # Handle default flag change
                if update_data.get('is_default') and not template.is_default:
                    ReportTemplate.objects.filter(report_type=template.report_type, is_default=True).update(is_default=False)

                for field, value in update_data.items():
                    if hasattr(template, field) and field != 'template_file':
                        setattr(template, field, value)
                # Handle file update separately if needed
                if 'template_file' in update_data:
                    template.template_file = update_data['template_file']
                template.full_clean()
                template.save()
                return template
        except ValidationError as e:
            raise

    @staticmethod
    def delete_template(template: ReportTemplate, soft_delete: bool = True) -> bool:
        try:
            if soft_delete:
                template.is_active = False
                template.save()
            else:
                template.delete()
            return True
        except Exception:
            return False

    @staticmethod
    def set_as_default(template: ReportTemplate) -> ReportTemplate:
        with transaction.atomic():
            ReportTemplate.objects.filter(report_type=template.report_type, is_default=True).update(is_default=False)
            template.is_default = True
            template.save()
            return template