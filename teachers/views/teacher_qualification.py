import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from teachers.models import TeacherQualification
from teachers.serializers.teacher_qualification import (
    TeacherQualificationMinimalSerializer,
    TeacherQualificationCreateSerializer,
    TeacherQualificationUpdateSerializer,
    TeacherQualificationDisplaySerializer,
)
from teachers.services.teacher_qualification import TeacherQualificationService

logger = logging.getLogger(__name__)

def can_view_qualification(user, qual):
    if user.is_staff:
        return True
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        return qual.teacher == user.teacher_profile
    if user.role == 'ADMIN':
        return True
    return False

def can_manage_qualification(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TeacherQualificationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    teacher = serializers.IntegerField()
    qualification_name = serializers.CharField()
    date_earned = serializers.DateField()

class TeacherQualificationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherQualificationCreateResponseData(allow_null=True)

class TeacherQualificationUpdateResponseData(serializers.Serializer):
    qualification = TeacherQualificationDisplaySerializer()

class TeacherQualificationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherQualificationUpdateResponseData(allow_null=True)

class TeacherQualificationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TeacherQualificationDetailResponseData(serializers.Serializer):
    qualification = TeacherQualificationDisplaySerializer()

class TeacherQualificationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherQualificationDetailResponseData(allow_null=True)

class TeacherQualificationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TeacherQualificationMinimalSerializer(many=True)

class TeacherQualificationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeacherQualificationListResponseData()

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

class TeacherQualificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Teachers - Qualifications"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="teacher_id", type=int, description="Filter by teacher ID", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active (non-expired) qualifications", required=False),
        ],
        responses={200: TeacherQualificationListResponseSerializer},
        description="List teacher qualifications (admin/hr see all, teachers see their own)."
    )
    def get(self, request):
        user = request.user
        teacher_id = request.query_params.get("teacher_id")
        active_only = request.query_params.get("active_only", "false").lower() == "true"

        if user.is_staff or can_manage_qualification(user):
            queryset = TeacherQualification.objects.all().select_related('teacher')
        else:
            if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                queryset = TeacherQualification.objects.filter(teacher=user.teacher_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if active_only:
            from datetime import date
            queryset = queryset.filter(expiry_date__gte=date.today())

        queryset = queryset.order_by('-date_earned')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, TeacherQualificationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Teacher qualifications retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Teachers - Qualifications"],
        request=TeacherQualificationCreateSerializer,
        responses={201: TeacherQualificationCreateResponseSerializer, 400: TeacherQualificationCreateResponseSerializer, 403: TeacherQualificationCreateResponseSerializer},
        description="Create a teacher qualification (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_qualification(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = TeacherQualificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            qual = serializer.save()
            return Response({
                "status": True,
                "message": "Qualification created.",
                "data": {
                    "id": qual.id,
                    "teacher": qual.teacher.id,
                    "qualification_name": qual.qualification_name,
                    "date_earned": qual.date_earned,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeacherQualificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, qual_id):
        try:
            return TeacherQualification.objects.select_related('teacher').get(id=qual_id)
        except TeacherQualification.DoesNotExist:
            return None

    @extend_schema(
        tags=["Teachers - Qualifications"],
        responses={200: TeacherQualificationDetailResponseSerializer, 404: TeacherQualificationDetailResponseSerializer, 403: TeacherQualificationDetailResponseSerializer},
        description="Retrieve a single teacher qualification by ID."
    )
    def get(self, request, qual_id):
        qual = self.get_object(qual_id)
        if not qual:
            return Response({
                "status": False,
                "message": "Qualification not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_qualification(request.user, qual):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = TeacherQualificationDisplaySerializer(qual, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Qualification retrieved.",
            "data": {"qualification": data}
        })

    @extend_schema(
        tags=["Teachers - Qualifications"],
        request=TeacherQualificationUpdateSerializer,
        responses={200: TeacherQualificationUpdateResponseSerializer, 400: TeacherQualificationUpdateResponseSerializer, 403: TeacherQualificationUpdateResponseSerializer},
        description="Update a teacher qualification (admin/hr only)."
    )
    @transaction.atomic
    def put(self, request, qual_id):
        return self._update(request, qual_id, partial=False)

    @extend_schema(
        tags=["Teachers - Qualifications"],
        request=TeacherQualificationUpdateSerializer,
        responses={200: TeacherQualificationUpdateResponseSerializer, 400: TeacherQualificationUpdateResponseSerializer, 403: TeacherQualificationUpdateResponseSerializer},
        description="Partially update a teacher qualification."
    )
    @transaction.atomic
    def patch(self, request, qual_id):
        return self._update(request, qual_id, partial=True)

    def _update(self, request, qual_id, partial):
        if not can_manage_qualification(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        qual = self.get_object(qual_id)
        if not qual:
            return Response({
                "status": False,
                "message": "Qualification not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TeacherQualificationUpdateSerializer(qual, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = TeacherQualificationDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Qualification updated.",
                "data": {"qualification": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Teachers - Qualifications"],
        responses={200: TeacherQualificationDeleteResponseSerializer, 403: TeacherQualificationDeleteResponseSerializer, 404: TeacherQualificationDeleteResponseSerializer},
        description="Delete a teacher qualification (admin only)."
    )
    @transaction.atomic
    def delete(self, request, qual_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        qual = self.get_object(qual_id)
        if not qual:
            return Response({
                "status": False,
                "message": "Qualification not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = TeacherQualificationService.delete_qualification(qual)
        if success:
            return Response({
                "status": True,
                "message": "Qualification deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete qualification.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)