from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Dict, Any
from datetime import date

from ..models.student_document import StudentDocument
from ..models.student import Student
from ...users.models import User

class StudentDocumentService:
    """Service for StudentDocument model operations"""

    @staticmethod
    def create_document(
        student: Student,
        document_type: str,
        title: str,
        file_url: str,
        uploaded_by: User,
        expiry_date: Optional[date] = None,
        notes: str = ""
    ) -> StudentDocument:
        try:
            with transaction.atomic():
                document = StudentDocument(
                    student=student,
                    document_type=document_type,
                    title=title,
                    file_url=file_url,
                    uploaded_by=uploaded_by,
                    expiry_date=expiry_date,
                    notes=notes,
                    verified=False
                )
                document.full_clean()
                document.save()
                return document
        except ValidationError as e:
            raise

    @staticmethod
    def get_document_by_id(document_id: int) -> Optional[StudentDocument]:
        try:
            return StudentDocument.objects.get(id=document_id)
        except StudentDocument.DoesNotExist:
            return None

    @staticmethod
    def get_documents_by_student(student_id: int) -> List[StudentDocument]:
        return StudentDocument.objects.filter(student_id=student_id).order_by('-created_at')

    @staticmethod
    def verify_document(document: StudentDocument) -> StudentDocument:
        document.verified = True
        document.verified_at = timezone.now()
        document.save()
        return document

    @staticmethod
    def delete_document(document: StudentDocument) -> bool:
        try:
            document.delete()
            return True
        except Exception:
            return False