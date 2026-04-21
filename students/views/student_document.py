import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from students.models import StudentDocument
from students.serializers.student_document import (
    StudentDocumentMinimalSerializer,
    StudentDocumentCreateSerializer,
    StudentDocumentUpdateSerializer,
    StudentDocumentDisplaySerializer,
)
from students.services.student_document import StudentDocumentService

logger = logging.getLogger(__name__)

def can_view_document(user, document):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return document.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return document.student in [sp.student for sp in user.parent_profile.students.all()]
    return False

def can_manage_document(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class StudentDocumentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    document_type = serializers.CharField()
    title = serializers.CharField()

class StudentDocumentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentDocumentCreateResponseData(allow_null=True)

class StudentDocumentUpdateResponseData(serializers.Serializer):
    document = StudentDocumentDisplaySerializer()

class StudentDocumentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentDocumentUpdateResponseData(allow_null=True)

class StudentDocumentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class StudentDocumentDetailResponseData(serializers.Serializer):
    document = StudentDocumentDisplaySerializer()

class StudentDocumentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentDocumentDetailResponseData(allow_null=True)

class StudentDocumentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = StudentDocumentMinimalSerializer(many=True)

class StudentDocumentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentDocumentListResponseData()

def wrap_paginated_data(paginator, page, request, serializer_class):
    serializer = serializer_class(page, many=True, context={'request': request})
    return {
        'page': paginator.page.number,
        'hasNext': paginator.page.has_next(),
        'hasPrev': paginator.page.has_previous(),
        'count': paginator.page.paginator.count,
        'next': paginator.get_next_link(),
        'previous': paginator.get_previous_link(),
        'results': serializer.data,
    }

# ----------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------

class StudentDocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Students - Documents"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="document_type", type=str, description="Filter by document type", required=False),
        ],
        responses={200: StudentDocumentListResponseSerializer},
        description="List student documents (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        document_type = request.query_params.get("document_type")

        if user.is_staff or can_manage_document(user):
            queryset = StudentDocument.objects.all().select_related('student', 'uploaded_by')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = StudentDocument.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = StudentDocument.objects.filter(student_id__in=child_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if document_type:
            queryset = queryset.filter(document_type=document_type)

        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, StudentDocumentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Student documents retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Students - Documents"],
        request=StudentDocumentCreateSerializer,
        responses={201: StudentDocumentCreateResponseSerializer, 400: StudentDocumentCreateResponseSerializer, 403: StudentDocumentCreateResponseSerializer},
        description="Upload a student document (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_document(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = request.data.copy()
        data['uploaded_by_id'] = request.user.id
        serializer = StudentDocumentCreateSerializer(data=data)
        if serializer.is_valid():
            document = serializer.save()
            return Response({
                "status": True,
                "message": "Document uploaded.",
                "data": {
                    "id": document.id,
                    "student": document.student.id,
                    "document_type": document.document_type,
                    "title": document.title,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentDocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, doc_id):
        try:
            return StudentDocument.objects.select_related('student', 'uploaded_by').get(id=doc_id)
        except StudentDocument.DoesNotExist:
            return None

    @extend_schema(
        tags=["Students - Documents"],
        responses={200: StudentDocumentDetailResponseSerializer, 404: StudentDocumentDetailResponseSerializer, 403: StudentDocumentDetailResponseSerializer},
        description="Retrieve a single student document by ID."
    )
    def get(self, request, doc_id):
        document = self.get_object(doc_id)
        if not document:
            return Response({
                "status": False,
                "message": "Document not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_document(request.user, document):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = StudentDocumentDisplaySerializer(document, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Document retrieved.",
            "data": {"document": data}
        })

    @extend_schema(
        tags=["Students - Documents"],
        request=StudentDocumentUpdateSerializer,
        responses={200: StudentDocumentUpdateResponseSerializer, 400: StudentDocumentUpdateResponseSerializer, 403: StudentDocumentUpdateResponseSerializer},
        description="Update a student document (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, doc_id):
        return self._update(request, doc_id, partial=False)

    @extend_schema(
        tags=["Students - Documents"],
        request=StudentDocumentUpdateSerializer,
        responses={200: StudentDocumentUpdateResponseSerializer, 400: StudentDocumentUpdateResponseSerializer, 403: StudentDocumentUpdateResponseSerializer},
        description="Partially update a student document."
    )
    @transaction.atomic
    def patch(self, request, doc_id):
        return self._update(request, doc_id, partial=True)

    def _update(self, request, doc_id, partial):
        if not can_manage_document(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        document = self.get_object(doc_id)
        if not document:
            return Response({
                "status": False,
                "message": "Document not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentDocumentUpdateSerializer(document, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = StudentDocumentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Document updated.",
                "data": {"document": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Students - Documents"],
        responses={200: StudentDocumentDeleteResponseSerializer, 403: StudentDocumentDeleteResponseSerializer, 404: StudentDocumentDeleteResponseSerializer},
        description="Delete a student document (admin only)."
    )
    @transaction.atomic
    def delete(self, request, doc_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        document = self.get_object(doc_id)
        if not document:
            return Response({
                "status": False,
                "message": "Document not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = StudentDocumentService.delete_document(document)
        if success:
            return Response({
                "status": True,
                "message": "Document deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete document.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentDocumentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Students - Documents"],
        responses={200: StudentDocumentUpdateResponseSerializer, 403: StudentDocumentUpdateResponseSerializer, 404: StudentDocumentUpdateResponseSerializer},
        description="Verify a student document (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request, doc_id):
        if not can_manage_document(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        document = StudentDocumentService.get_document_by_id(doc_id)
        if not document:
            return Response({
                "status": False,
                "message": "Document not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if document.verified:
            return Response({
                "status": False,
                "message": "Document already verified.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = StudentDocumentService.verify_document(document)
        data = StudentDocumentDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Document verified.",
            "data": {"document": data}
        })