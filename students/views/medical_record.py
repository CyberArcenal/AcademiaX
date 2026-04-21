import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from students.models import MedicalRecord
from students.serializers.medical_record import (
    MedicalRecordMinimalSerializer,
    MedicalRecordCreateSerializer,
    MedicalRecordUpdateSerializer,
    MedicalRecordDisplaySerializer,
)
from students.services.medical_record import MedicalRecordService

logger = logging.getLogger(__name__)

def can_view_medical_record(user, record):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return record.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        # Parent can see their child's medical record
        return record.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        # Teachers might have limited access? For now, allow only if they have student in class
        teacher = user.teacher_profile
        sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
        from enrollments.models import Enrollment
        student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
        return record.student.id in student_ids
    return False

def can_manage_medical_record(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR', 'NURSE'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class MedicalRecordCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    blood_type = serializers.CharField()

class MedicalRecordCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MedicalRecordCreateResponseData(allow_null=True)

class MedicalRecordUpdateResponseData(serializers.Serializer):
    record = MedicalRecordDisplaySerializer()

class MedicalRecordUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MedicalRecordUpdateResponseData(allow_null=True)

class MedicalRecordDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class MedicalRecordDetailResponseData(serializers.Serializer):
    record = MedicalRecordDisplaySerializer()

class MedicalRecordDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MedicalRecordDetailResponseData(allow_null=True)

class MedicalRecordListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = MedicalRecordMinimalSerializer(many=True)

class MedicalRecordListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MedicalRecordListResponseData()

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

class MedicalRecordListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Students - Medical Records"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
        ],
        responses={200: MedicalRecordListResponseSerializer},
        description="List medical records (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")

        if user.is_staff or can_manage_medical_record(user):
            queryset = MedicalRecord.objects.all().select_related('student')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = MedicalRecord.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = MedicalRecord.objects.filter(student_id__in=child_ids)
            elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                teacher = user.teacher_profile
                sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                from enrollments.models import Enrollment
                student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
                queryset = MedicalRecord.objects.filter(student_id__in=student_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, MedicalRecordMinimalSerializer)
        return Response({
            "status": True,
            "message": "Medical records retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Students - Medical Records"],
        request=MedicalRecordCreateSerializer,
        responses={201: MedicalRecordCreateResponseSerializer, 400: MedicalRecordCreateResponseSerializer, 403: MedicalRecordCreateResponseSerializer},
        description="Create a medical record (admin/registrar/nurse only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_medical_record(request.user):
            return Response({
                "status": False,
                "message": "Admin, registrar, or nurse permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = MedicalRecordCreateSerializer(data=request.data)
        if serializer.is_valid():
            record = serializer.save()
            return Response({
                "status": True,
                "message": "Medical record created.",
                "data": {
                    "id": record.id,
                    "student": record.student.id,
                    "blood_type": record.blood_type,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MedicalRecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, record_id):
        try:
            return MedicalRecord.objects.select_related('student').get(id=record_id)
        except MedicalRecord.DoesNotExist:
            return None

    @extend_schema(
        tags=["Students - Medical Records"],
        responses={200: MedicalRecordDetailResponseSerializer, 404: MedicalRecordDetailResponseSerializer, 403: MedicalRecordDetailResponseSerializer},
        description="Retrieve a single medical record by ID."
    )
    def get(self, request, record_id):
        record = self.get_object(record_id)
        if not record:
            return Response({
                "status": False,
                "message": "Medical record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_medical_record(request.user, record):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = MedicalRecordDisplaySerializer(record, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Medical record retrieved.",
            "data": {"record": data}
        })

    @extend_schema(
        tags=["Students - Medical Records"],
        request=MedicalRecordUpdateSerializer,
        responses={200: MedicalRecordUpdateResponseSerializer, 400: MedicalRecordUpdateResponseSerializer, 403: MedicalRecordUpdateResponseSerializer},
        description="Update a medical record (admin/registrar/nurse only)."
    )
    @transaction.atomic
    def put(self, request, record_id):
        return self._update(request, record_id, partial=False)

    @extend_schema(
        tags=["Students - Medical Records"],
        request=MedicalRecordUpdateSerializer,
        responses={200: MedicalRecordUpdateResponseSerializer, 400: MedicalRecordUpdateResponseSerializer, 403: MedicalRecordUpdateResponseSerializer},
        description="Partially update a medical record."
    )
    @transaction.atomic
    def patch(self, request, record_id):
        return self._update(request, record_id, partial=True)

    def _update(self, request, record_id, partial):
        if not can_manage_medical_record(request.user):
            return Response({
                "status": False,
                "message": "Admin, registrar, or nurse permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        record = self.get_object(record_id)
        if not record:
            return Response({
                "status": False,
                "message": "Medical record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = MedicalRecordUpdateSerializer(record, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = MedicalRecordDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Medical record updated.",
                "data": {"record": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Students - Medical Records"],
        responses={200: MedicalRecordDeleteResponseSerializer, 403: MedicalRecordDeleteResponseSerializer, 404: MedicalRecordDeleteResponseSerializer},
        description="Delete a medical record (admin only)."
    )
    @transaction.atomic
    def delete(self, request, record_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        record = self.get_object(record_id)
        if not record:
            return Response({
                "status": False,
                "message": "Medical record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = MedicalRecordService.delete_medical_record(record)
        if success:
            return Response({
                "status": True,
                "message": "Medical record deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete medical record.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)