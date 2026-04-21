import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from teachers.models import Specialization
from teachers.serializers.specialization import (
    SpecializationMinimalSerializer,
    SpecializationCreateSerializer,
    SpecializationUpdateSerializer,
    SpecializationDisplaySerializer,
)
from teachers.services.specialization import SpecializationService

logger = logging.getLogger(__name__)

def can_view_specialization(user, spec):
    if user.is_staff:
        return True
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        return spec.teacher == user.teacher_profile
    if user.role == 'ADMIN':
        return True
    return False

def can_manage_specialization(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class SpecializationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    teacher = serializers.IntegerField()
    subject = serializers.IntegerField()
    is_primary = serializers.BooleanField()

class SpecializationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SpecializationCreateResponseData(allow_null=True)

class SpecializationUpdateResponseData(serializers.Serializer):
    specialization = SpecializationDisplaySerializer()

class SpecializationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SpecializationUpdateResponseData(allow_null=True)

class SpecializationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class SpecializationDetailResponseData(serializers.Serializer):
    specialization = SpecializationDisplaySerializer()

class SpecializationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SpecializationDetailResponseData(allow_null=True)

class SpecializationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SpecializationMinimalSerializer(many=True)

class SpecializationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SpecializationListResponseData()

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

class SpecializationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Teachers - Specializations"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="teacher_id", type=int, description="Filter by teacher ID", required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject ID", required=False),
        ],
        responses={200: SpecializationListResponseSerializer},
        description="List teacher specializations (admin/hr see all, teachers see their own)."
    )
    def get(self, request):
        user = request.user
        teacher_id = request.query_params.get("teacher_id")
        subject_id = request.query_params.get("subject_id")

        if user.is_staff or can_manage_specialization(user):
            queryset = Specialization.objects.all().select_related('teacher', 'subject')
        else:
            if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                queryset = Specialization.objects.filter(teacher=user.teacher_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, SpecializationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Specializations retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Teachers - Specializations"],
        request=SpecializationCreateSerializer,
        responses={201: SpecializationCreateResponseSerializer, 400: SpecializationCreateResponseSerializer, 403: SpecializationCreateResponseSerializer},
        description="Create a teacher specialization (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_specialization(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = SpecializationCreateSerializer(data=request.data)
        if serializer.is_valid():
            spec = serializer.save()
            return Response({
                "status": True,
                "message": "Specialization created.",
                "data": {
                    "id": spec.id,
                    "teacher": spec.teacher.id,
                    "subject": spec.subject.id,
                    "is_primary": spec.is_primary,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SpecializationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, spec_id):
        try:
            return Specialization.objects.select_related('teacher', 'subject').get(id=spec_id)
        except Specialization.DoesNotExist:
            return None

    @extend_schema(
        tags=["Teachers - Specializations"],
        responses={200: SpecializationDetailResponseSerializer, 404: SpecializationDetailResponseSerializer, 403: SpecializationDetailResponseSerializer},
        description="Retrieve a single specialization by ID."
    )
    def get(self, request, spec_id):
        spec = self.get_object(spec_id)
        if not spec:
            return Response({
                "status": False,
                "message": "Specialization not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_specialization(request.user, spec):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = SpecializationDisplaySerializer(spec, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Specialization retrieved.",
            "data": {"specialization": data}
        })

    @extend_schema(
        tags=["Teachers - Specializations"],
        request=SpecializationUpdateSerializer,
        responses={200: SpecializationUpdateResponseSerializer, 400: SpecializationUpdateResponseSerializer, 403: SpecializationUpdateResponseSerializer},
        description="Update a specialization (admin/hr only)."
    )
    @transaction.atomic
    def put(self, request, spec_id):
        return self._update(request, spec_id, partial=False)

    @extend_schema(
        tags=["Teachers - Specializations"],
        request=SpecializationUpdateSerializer,
        responses={200: SpecializationUpdateResponseSerializer, 400: SpecializationUpdateResponseSerializer, 403: SpecializationUpdateResponseSerializer},
        description="Partially update a specialization."
    )
    @transaction.atomic
    def patch(self, request, spec_id):
        return self._update(request, spec_id, partial=True)

    def _update(self, request, spec_id, partial):
        if not can_manage_specialization(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        spec = self.get_object(spec_id)
        if not spec:
            return Response({
                "status": False,
                "message": "Specialization not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = SpecializationUpdateSerializer(spec, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = SpecializationDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Specialization updated.",
                "data": {"specialization": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Teachers - Specializations"],
        responses={200: SpecializationDeleteResponseSerializer, 403: SpecializationDeleteResponseSerializer, 404: SpecializationDeleteResponseSerializer},
        description="Delete a specialization (admin only)."
    )
    @transaction.atomic
    def delete(self, request, spec_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        spec = self.get_object(spec_id)
        if not spec:
            return Response({
                "status": False,
                "message": "Specialization not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = SpecializationService.delete_specialization(spec)
        if success:
            return Response({
                "status": True,
                "message": "Specialization deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete specialization.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)