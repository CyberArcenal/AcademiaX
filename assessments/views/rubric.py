import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from assessments.models import RubricCriterion, RubricLevel
from assessments.serializers.rubric import (
    RubricCriterionMinimalSerializer,
    RubricCriterionCreateSerializer,
    RubricCriterionUpdateSerializer,
    RubricCriterionDisplaySerializer,
    RubricLevelMinimalSerializer,
    RubricLevelCreateSerializer,
    RubricLevelUpdateSerializer,
    RubricLevelDisplaySerializer,
)
from assessments.services.rubric import RubricCriterionService, RubricLevelService
from assessments.services.assessment import AssessmentService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# Helper to check if user can modify assessment (teacher or admin)
def can_modify_assessment(user, assessment):
    if user.is_staff:
        return True
    if assessment.teacher and assessment.teacher.user == user:
        return True
    return False

# ----------------------------------------------------------------------
# Response serializers for RubricCriterion
# ----------------------------------------------------------------------

class CriterionCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    assessment = serializers.IntegerField()
    name = serializers.CharField()

class CriterionCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CriterionCreateResponseData(allow_null=True)

class CriterionUpdateResponseData(serializers.Serializer):
    criterion = RubricCriterionDisplaySerializer()

class CriterionUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CriterionUpdateResponseData(allow_null=True)

class CriterionDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class CriterionDetailResponseData(serializers.Serializer):
    criterion = RubricCriterionDisplaySerializer()

class CriterionDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CriterionDetailResponseData(allow_null=True)

class CriterionListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = RubricCriterionMinimalSerializer(many=True)

class CriterionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CriterionListResponseData()

# ----------------------------------------------------------------------
# Response serializers for RubricLevel
# ----------------------------------------------------------------------

class LevelCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    criterion = serializers.IntegerField()
    level_name = serializers.CharField()

class LevelCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LevelCreateResponseData(allow_null=True)

class LevelUpdateResponseData(serializers.Serializer):
    level = RubricLevelDisplaySerializer()

class LevelUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LevelUpdateResponseData(allow_null=True)

class LevelDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class LevelDetailResponseData(serializers.Serializer):
    level = RubricLevelDisplaySerializer()

class LevelDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LevelDetailResponseData(allow_null=True)

class LevelListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = RubricLevelMinimalSerializer(many=True)

class LevelListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LevelListResponseData()

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
# RubricCriterion Views
# ----------------------------------------------------------------------

class RubricCriterionListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Assessments - Rubric Criteria"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="assessment_id", type=int, description="Filter by assessment ID", required=False),
        ],
        responses={200: CriterionListResponseSerializer},
        description="List rubric criteria, optionally filtered by assessment."
    )
    def get(self, request):
        assessment_id = request.query_params.get("assessment_id")
        if assessment_id:
            criteria = RubricCriterionService.get_criteria_by_assessment(assessment_id)
        else:
            criteria = RubricCriterion.objects.all().select_related('assessment').order_by('order')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(criteria, request)
        data = wrap_paginated_data(paginator, page, request, RubricCriterionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Criteria retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments - Rubric Criteria"],
        request=RubricCriterionCreateSerializer,
        responses={201: CriterionCreateResponseSerializer, 400: CriterionCreateResponseSerializer},
        description="Create a rubric criterion (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = RubricCriterionCreateSerializer(data=request.data)
        if serializer.is_valid():
            assessment = serializer.validated_data.get('assessment')
            if not can_modify_assessment(request.user, assessment):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            criterion = serializer.save()
            return Response({
                "status": True,
                "message": "Criterion created.",
                "data": {
                    "id": criterion.id,
                    "assessment": criterion.assessment.id,
                    "name": criterion.name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RubricCriterionDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, criterion_id):
        return RubricCriterionService.get_criterion_by_id(criterion_id)

    @extend_schema(
        tags=["Assessments - Rubric Criteria"],
        responses={200: CriterionDetailResponseSerializer, 404: CriterionDetailResponseSerializer},
        description="Retrieve a single rubric criterion by ID."
    )
    def get(self, request, criterion_id):
        criterion = self.get_object(criterion_id)
        if not criterion:
            return Response({
                "status": False,
                "message": "Criterion not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = RubricCriterionDisplaySerializer(criterion, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Criterion retrieved.",
            "data": {"criterion": data}
        })

    @extend_schema(
        tags=["Assessments - Rubric Criteria"],
        request=RubricCriterionUpdateSerializer,
        responses={200: CriterionUpdateResponseSerializer, 400: CriterionUpdateResponseSerializer, 403: CriterionUpdateResponseSerializer},
        description="Update a rubric criterion (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, criterion_id):
        return self._update(request, criterion_id, partial=False)

    @extend_schema(
        tags=["Assessments - Rubric Criteria"],
        request=RubricCriterionUpdateSerializer,
        responses={200: CriterionUpdateResponseSerializer, 400: CriterionUpdateResponseSerializer, 403: CriterionUpdateResponseSerializer},
        description="Partially update a rubric criterion."
    )
    @transaction.atomic
    def patch(self, request, criterion_id):
        return self._update(request, criterion_id, partial=True)

    def _update(self, request, criterion_id, partial):
        criterion = self.get_object(criterion_id)
        if not criterion:
            return Response({
                "status": False,
                "message": "Criterion not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not can_modify_assessment(user, criterion.assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = RubricCriterionUpdateSerializer(criterion, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = RubricCriterionDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Criterion updated.",
                "data": {"criterion": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Assessments - Rubric Criteria"],
        responses={200: CriterionDeleteResponseSerializer, 403: CriterionDeleteResponseSerializer, 404: CriterionDeleteResponseSerializer},
        description="Delete a rubric criterion (teacher or admin only)."
    )
    @transaction.atomic
    def delete(self, request, criterion_id):
        criterion = self.get_object(criterion_id)
        if not criterion:
            return Response({
                "status": False,
                "message": "Criterion not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not can_modify_assessment(user, criterion.assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = RubricCriterionService.delete_criterion(criterion)
        if success:
            return Response({
                "status": True,
                "message": "Criterion deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete criterion.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ----------------------------------------------------------------------
# RubricLevel Views
# ----------------------------------------------------------------------

class RubricLevelListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Assessments - Rubric Levels"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="criterion_id", type=int, description="Filter by criterion ID", required=False),
        ],
        responses={200: LevelListResponseSerializer},
        description="List rubric levels, optionally filtered by criterion."
    )
    def get(self, request):
        criterion_id = request.query_params.get("criterion_id")
        if criterion_id:
            levels = RubricLevelService.get_levels_by_criterion(criterion_id)
        else:
            levels = RubricLevel.objects.all().select_related('criterion').order_by('-points')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(levels, request)
        data = wrap_paginated_data(paginator, page, request, RubricLevelMinimalSerializer)
        return Response({
            "status": True,
            "message": "Levels retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments - Rubric Levels"],
        request=RubricLevelCreateSerializer,
        responses={201: LevelCreateResponseSerializer, 400: LevelCreateResponseSerializer},
        description="Create a rubric level (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = RubricLevelCreateSerializer(data=request.data)
        if serializer.is_valid():
            criterion = serializer.validated_data.get('criterion')
            if not can_modify_assessment(request.user, criterion.assessment):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            level = serializer.save()
            return Response({
                "status": True,
                "message": "Level created.",
                "data": {
                    "id": level.id,
                    "criterion": level.criterion.id,
                    "level_name": level.level_name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RubricLevelDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, level_id):
        return RubricLevelService.get_level_by_id(level_id)

    @extend_schema(
        tags=["Assessments - Rubric Levels"],
        responses={200: LevelDetailResponseSerializer, 404: LevelDetailResponseSerializer},
        description="Retrieve a single rubric level by ID."
    )
    def get(self, request, level_id):
        level = self.get_object(level_id)
        if not level:
            return Response({
                "status": False,
                "message": "Level not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = RubricLevelDisplaySerializer(level, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Level retrieved.",
            "data": {"level": data}
        })

    @extend_schema(
        tags=["Assessments - Rubric Levels"],
        request=RubricLevelUpdateSerializer,
        responses={200: LevelUpdateResponseSerializer, 400: LevelUpdateResponseSerializer, 403: LevelUpdateResponseSerializer},
        description="Update a rubric level (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, level_id):
        return self._update(request, level_id, partial=False)

    @extend_schema(
        tags=["Assessments - Rubric Levels"],
        request=RubricLevelUpdateSerializer,
        responses={200: LevelUpdateResponseSerializer, 400: LevelUpdateResponseSerializer, 403: LevelUpdateResponseSerializer},
        description="Partially update a rubric level."
    )
    @transaction.atomic
    def patch(self, request, level_id):
        return self._update(request, level_id, partial=True)

    def _update(self, request, level_id, partial):
        level = self.get_object(level_id)
        if not level:
            return Response({
                "status": False,
                "message": "Level not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not can_modify_assessment(user, level.criterion.assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = RubricLevelUpdateSerializer(level, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = RubricLevelDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Level updated.",
                "data": {"level": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Assessments - Rubric Levels"],
        responses={200: LevelDeleteResponseSerializer, 403: LevelDeleteResponseSerializer, 404: LevelDeleteResponseSerializer},
        description="Delete a rubric level (teacher or admin only)."
    )
    @transaction.atomic
    def delete(self, request, level_id):
        level = self.get_object(level_id)
        if not level:
            return Response({
                "status": False,
                "message": "Level not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not can_modify_assessment(user, level.criterion.assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = RubricLevelService.delete_level(level)
        if success:
            return Response({
                "status": True,
                "message": "Level deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete level.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)