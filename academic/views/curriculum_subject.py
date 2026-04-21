import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from academic.models import CurriculumSubject
from academic.serializers.curriculum_subject import (
    CurriculumSubjectMinimalSerializer,
    CurriculumSubjectCreateSerializer,
    CurriculumSubjectUpdateSerializer,
    CurriculumSubjectDisplaySerializer,
)
from academic.services.curriculum_subject import CurriculumSubjectService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class CurriculumSubjectCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    curriculum = serializers.IntegerField()
    subject = serializers.IntegerField()

class CurriculumSubjectCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumSubjectCreateResponseData(allow_null=True)

class CurriculumSubjectUpdateResponseData(serializers.Serializer):
    curriculum_subject = CurriculumSubjectDisplaySerializer()

class CurriculumSubjectUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumSubjectUpdateResponseData(allow_null=True)

class CurriculumSubjectDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class CurriculumSubjectDetailResponseData(serializers.Serializer):
    curriculum_subject = CurriculumSubjectDisplaySerializer()

class CurriculumSubjectDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumSubjectDetailResponseData(allow_null=True)

class CurriculumSubjectListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = CurriculumSubjectMinimalSerializer(many=True)

class CurriculumSubjectListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumSubjectListResponseData()

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

class CurriculumSubjectListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Academic - Curriculum Subjects"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="curriculum_id", type=int, description="Filter by curriculum ID", required=False),
        ],
        responses={200: CurriculumSubjectListResponseSerializer},
        description="List curriculum-subject links, optionally filtered by curriculum."
    )
    def get(self, request):
        curriculum_id = request.query_params.get("curriculum_id")
        if curriculum_id:
            items = CurriculumSubjectService.get_subjects_by_curriculum(curriculum_id)
        else:
            items = CurriculumSubject.objects.all().select_related('curriculum', 'subject')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(items, request)
        data = wrap_paginated_data(paginator, page, request, CurriculumSubjectMinimalSerializer)
        return Response({
            "status": True,
            "message": "Curriculum subjects retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Academic - Curriculum Subjects"],
        request=CurriculumSubjectCreateSerializer,
        responses={201: CurriculumSubjectCreateResponseSerializer, 400: CurriculumSubjectCreateResponseSerializer},
        description="Add a subject to a curriculum."
    )
    @transaction.atomic
    def post(self, request):
        serializer = CurriculumSubjectCreateSerializer(data=request.data)
        if serializer.is_valid():
            cs = serializer.save()
            return Response({
                "status": True,
                "message": "Subject added to curriculum.",
                "data": {
                    "id": cs.id,
                    "curriculum": cs.curriculum.id,
                    "subject": cs.subject.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CurriculumSubjectDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, cs_id):
        return CurriculumSubjectService.get_curriculum_subject_by_id(cs_id)

    @extend_schema(
        tags=["Academic - Curriculum Subjects"],
        responses={200: CurriculumSubjectDetailResponseSerializer, 404: CurriculumSubjectDetailResponseSerializer},
        description="Retrieve a single curriculum-subject link by ID."
    )
    def get(self, request, cs_id):
        cs = self.get_object(cs_id)
        if not cs:
            return Response({
                "status": False,
                "message": "Curriculum subject not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = CurriculumSubjectDisplaySerializer(cs, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Curriculum subject retrieved.",
            "data": {"curriculum_subject": data}
        })

    @extend_schema(
        tags=["Academic - Curriculum Subjects"],
        request=CurriculumSubjectUpdateSerializer,
        responses={200: CurriculumSubjectUpdateResponseSerializer, 400: CurriculumSubjectUpdateResponseSerializer, 403: CurriculumSubjectUpdateResponseSerializer},
        description="Update a curriculum-subject link."
    )
    @transaction.atomic
    def put(self, request, cs_id):
        return self._update(request, cs_id, partial=False)

    @extend_schema(
        tags=["Academic - Curriculum Subjects"],
        request=CurriculumSubjectUpdateSerializer,
        responses={200: CurriculumSubjectUpdateResponseSerializer, 400: CurriculumSubjectUpdateResponseSerializer, 403: CurriculumSubjectUpdateResponseSerializer},
        description="Partially update a curriculum-subject link."
    )
    @transaction.atomic
    def patch(self, request, cs_id):
        return self._update(request, cs_id, partial=True)

    def _update(self, request, cs_id, partial):
        cs = self.get_object(cs_id)
        if not cs:
            return Response({
                "status": False,
                "message": "Curriculum subject not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = CurriculumSubjectUpdateSerializer(cs, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = CurriculumSubjectDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Curriculum subject updated.",
                "data": {"curriculum_subject": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Academic - Curriculum Subjects"],
        responses={200: CurriculumSubjectDeleteResponseSerializer, 403: CurriculumSubjectDeleteResponseSerializer, 404: CurriculumSubjectDeleteResponseSerializer},
        description="Remove a subject from a curriculum (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, cs_id):
        cs = self.get_object(cs_id)
        if not cs:
            return Response({
                "status": False,
                "message": "Curriculum subject not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = CurriculumSubjectService.remove_subject_from_curriculum(cs)
        if success:
            return Response({
                "status": True,
                "message": "Subject removed from curriculum.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to remove subject.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurriculumSubjectReorderView(APIView):
    permission_classes = [IsAuthenticated]

    class ReorderSerializer(serializers.Serializer):
        subject_ids = serializers.ListField(child=serializers.IntegerField())

    @extend_schema(
        tags=["Academic - Curriculum Subjects"],
        request=ReorderSerializer,
        responses={200: serializers.Serializer, 400: serializers.Serializer},
        description="Reorder subjects within a curriculum by providing list of subject IDs in desired order."
    )
    @transaction.atomic
    def post(self, request, curriculum_id):
        serializer = self.ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        subject_ids = serializer.validated_data['subject_ids']
        success = CurriculumSubjectService.reorder_sequence(curriculum_id, subject_ids)
        if success:
            return Response({
                "status": True,
                "message": "Subjects reordered.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Reorder failed.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)