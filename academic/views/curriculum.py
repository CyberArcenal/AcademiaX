import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from academic.models import Curriculum
from academic.serializers.curriculum import (
    CurriculumMinimalSerializer,
    CurriculumCreateSerializer,
    CurriculumUpdateSerializer,
    CurriculumDisplaySerializer,
)
from academic.services.curriculum import CurriculumService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class CurriculumCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    academic_program = serializers.CharField()
    grade_level = serializers.CharField()
    year_effective = serializers.IntegerField()

class CurriculumCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumCreateResponseData(allow_null=True)

class CurriculumUpdateResponseData(serializers.Serializer):
    curriculum = CurriculumDisplaySerializer()

class CurriculumUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumUpdateResponseData(allow_null=True)

class CurriculumDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class CurriculumDetailResponseData(serializers.Serializer):
    curriculum = CurriculumDisplaySerializer()

class CurriculumDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumDetailResponseData(allow_null=True)

class CurriculumListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = CurriculumMinimalSerializer(many=True)

class CurriculumListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CurriculumListResponseData()

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

class CurriculumListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Academic - Curricula"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="program_id", type=int, description="Filter by academic program ID", required=False),
        ],
        responses={200: CurriculumListResponseSerializer},
        description="List curricula, optionally filtered by academic program."
    )
    def get(self, request):
        program_id = request.query_params.get("program_id")
        if program_id:
            curricula = CurriculumService.get_curricula_by_program(program_id)
        else:
            curricula = Curriculum.objects.all().order_by('-year_effective')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(curricula, request)
        data = wrap_paginated_data(paginator, page, request, CurriculumMinimalSerializer)
        return Response({
            "status": True,
            "message": "Curricula retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Academic - Curricula"],
        request=CurriculumCreateSerializer,
        responses={201: CurriculumCreateResponseSerializer, 400: CurriculumCreateResponseSerializer},
        description="Create a new curriculum (sets is_current automatically if specified)."
    )
    @transaction.atomic
    def post(self, request):
        serializer = CurriculumCreateSerializer(data=request.data)
        if serializer.is_valid():
            curriculum = serializer.save()
            return Response({
                "status": True,
                "message": "Curriculum created successfully.",
                "data": {
                    "id": curriculum.id,
                    "academic_program": curriculum.academic_program.code,
                    "grade_level": curriculum.grade_level,
                    "year_effective": curriculum.year_effective,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CurriculumDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, curriculum_id):
        return CurriculumService.get_curriculum_by_id(curriculum_id)

    @extend_schema(
        tags=["Academic - Curricula"],
        responses={200: CurriculumDetailResponseSerializer, 404: CurriculumDetailResponseSerializer},
        description="Retrieve a single curriculum by ID."
    )
    def get(self, request, curriculum_id):
        curriculum = self.get_object(curriculum_id)
        if not curriculum:
            return Response({
                "status": False,
                "message": "Curriculum not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = CurriculumDisplaySerializer(curriculum, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Curriculum retrieved.",
            "data": {"curriculum": data}
        })

    @extend_schema(
        tags=["Academic - Curricula"],
        request=CurriculumUpdateSerializer,
        responses={200: CurriculumUpdateResponseSerializer, 400: CurriculumUpdateResponseSerializer, 403: CurriculumUpdateResponseSerializer},
        description="Update a curriculum (can change is_current flag)."
    )
    @transaction.atomic
    def put(self, request, curriculum_id):
        return self._update(request, curriculum_id, partial=False)

    @extend_schema(
        tags=["Academic - Curricula"],
        request=CurriculumUpdateSerializer,
        responses={200: CurriculumUpdateResponseSerializer, 400: CurriculumUpdateResponseSerializer, 403: CurriculumUpdateResponseSerializer},
        description="Partially update a curriculum."
    )
    @transaction.atomic
    def patch(self, request, curriculum_id):
        return self._update(request, curriculum_id, partial=True)

    def _update(self, request, curriculum_id, partial):
        curriculum = self.get_object(curriculum_id)
        if not curriculum:
            return Response({
                "status": False,
                "message": "Curriculum not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = CurriculumUpdateSerializer(curriculum, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = CurriculumDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Curriculum updated successfully.",
                "data": {"curriculum": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Academic - Curricula"],
        parameters=[OpenApiParameter(name="hard", type=bool, required=False)],
        responses={200: CurriculumDeleteResponseSerializer, 403: CurriculumDeleteResponseSerializer, 404: CurriculumDeleteResponseSerializer},
        description="Delete a curriculum (soft delete by default)."
    )
    @transaction.atomic
    def delete(self, request, curriculum_id):
        curriculum = self.get_object(curriculum_id)
        if not curriculum:
            return Response({
                "status": False,
                "message": "Curriculum not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        hard = request.query_params.get("hard", "false").lower() == "true"
        success = CurriculumService.delete_curriculum(curriculum, soft_delete=not hard)
        if success:
            return Response({
                "status": True,
                "message": "Curriculum deleted successfully." + (" (permanent)" if hard else ""),
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete curriculum.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)