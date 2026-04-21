import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from classes.models import GradeLevel
from classes.serializers.grade_level import (
    GradeLevelMinimalSerializer,
    GradeLevelCreateSerializer,
    GradeLevelUpdateSerializer,
    GradeLevelDisplaySerializer,
)
from classes.services.grade_level import GradeLevelService
from global_utils.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_grade_level(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class GradeLevelCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    level = serializers.CharField()
    name = serializers.CharField()

class GradeLevelCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeLevelCreateResponseData(allow_null=True)

class GradeLevelUpdateResponseData(serializers.Serializer):
    grade_level = GradeLevelDisplaySerializer()

class GradeLevelUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeLevelUpdateResponseData(allow_null=True)

class GradeLevelDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class GradeLevelDetailResponseData(serializers.Serializer):
    grade_level = GradeLevelDisplaySerializer()

class GradeLevelDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeLevelDetailResponseData(allow_null=True)

class GradeLevelListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = GradeLevelMinimalSerializer(many=True)

class GradeLevelListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeLevelListResponseData()

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

class GradeLevelListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Grade Levels"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: GradeLevelListResponseSerializer},
        description="List all grade levels (ordered by level order)."
    )
    def get(self, request):
        grade_levels = GradeLevelService.get_all_grade_levels()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(grade_levels, request)
        data = wrap_paginated_data(paginator, page, request, GradeLevelMinimalSerializer)
        return Response({
            "status": True,
            "message": "Grade levels retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Classes - Grade Levels"],
        request=GradeLevelCreateSerializer,
        responses={201: GradeLevelCreateResponseSerializer, 400: GradeLevelCreateResponseSerializer, 403: GradeLevelCreateResponseSerializer},
        description="Create a new grade level (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_grade_level(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = GradeLevelCreateSerializer(data=request.data)
        if serializer.is_valid():
            grade_level = serializer.save()
            return Response({
                "status": True,
                "message": "Grade level created.",
                "data": {
                    "id": grade_level.id,
                    "level": grade_level.level,
                    "name": grade_level.name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GradeLevelDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, grade_level_id):
        return GradeLevelService.get_grade_level_by_id(grade_level_id)

    @extend_schema(
        tags=["Classes - Grade Levels"],
        responses={200: GradeLevelDetailResponseSerializer, 404: GradeLevelDetailResponseSerializer},
        description="Retrieve a single grade level by ID."
    )
    def get(self, request, grade_level_id):
        grade_level = self.get_object(grade_level_id)
        if not grade_level:
            return Response({
                "status": False,
                "message": "Grade level not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = GradeLevelDisplaySerializer(grade_level, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Grade level retrieved.",
            "data": {"grade_level": data}
        })

    @extend_schema(
        tags=["Classes - Grade Levels"],
        request=GradeLevelUpdateSerializer,
        responses={200: GradeLevelUpdateResponseSerializer, 400: GradeLevelUpdateResponseSerializer, 403: GradeLevelUpdateResponseSerializer},
        description="Update a grade level (admin only)."
    )
    @transaction.atomic
    def put(self, request, grade_level_id):
        return self._update(request, grade_level_id, partial=False)

    @extend_schema(
        tags=["Classes - Grade Levels"],
        request=GradeLevelUpdateSerializer,
        responses={200: GradeLevelUpdateResponseSerializer, 400: GradeLevelUpdateResponseSerializer, 403: GradeLevelUpdateResponseSerializer},
        description="Partially update a grade level."
    )
    @transaction.atomic
    def patch(self, request, grade_level_id):
        return self._update(request, grade_level_id, partial=True)

    def _update(self, request, grade_level_id, partial):
        if not can_manage_grade_level(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        grade_level = self.get_object(grade_level_id)
        if not grade_level:
            return Response({
                "status": False,
                "message": "Grade level not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = GradeLevelUpdateSerializer(grade_level, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = GradeLevelDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Grade level updated.",
                "data": {"grade_level": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Classes - Grade Levels"],
        responses={200: GradeLevelDeleteResponseSerializer, 403: GradeLevelDeleteResponseSerializer, 404: GradeLevelDeleteResponseSerializer},
        description="Delete a grade level (admin only)."
    )
    @transaction.atomic
    def delete(self, request, grade_level_id):
        if not can_manage_grade_level(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        grade_level = self.get_object(grade_level_id)
        if not grade_level:
            return Response({
                "status": False,
                "message": "Grade level not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = GradeLevelService.delete_grade_level(grade_level)
        if success:
            return Response({
                "status": True,
                "message": "Grade level deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete grade level.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GradeLevelReorderView(APIView):
    permission_classes = [IsAuthenticated]

    class ReorderSerializer(serializers.Serializer):
        level_ids = serializers.ListField(child=serializers.IntegerField())

    @extend_schema(
        tags=["Classes - Grade Levels"],
        request=ReorderSerializer,
        responses={200: serializers.Serializer, 400: serializers.Serializer, 403: serializers.Serializer},
        description="Reorder grade levels by providing list of IDs in desired order (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_grade_level(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        level_ids = serializer.validated_data['level_ids']
        success = GradeLevelService.reorder_grade_levels(level_ids)
        if success:
            return Response({
                "status": True,
                "message": "Grade levels reordered.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Reorder failed.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)