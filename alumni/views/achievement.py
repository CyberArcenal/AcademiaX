import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from alumni.models import AlumniAchievement
from alumni.serializers.achievement import (
    AlumniAchievementMinimalSerializer,
    AlumniAchievementCreateSerializer,
    AlumniAchievementUpdateSerializer,
    AlumniAchievementDisplaySerializer,
)
from alumni.services.achievement import AlumniAchievementService
from global_utils.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AchievementCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    alumni = serializers.IntegerField()
    title = serializers.CharField()

class AchievementCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AchievementCreateResponseData(allow_null=True)

class AchievementUpdateResponseData(serializers.Serializer):
    achievement = AlumniAchievementDisplaySerializer()

class AchievementUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AchievementUpdateResponseData(allow_null=True)

class AchievementDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AchievementDetailResponseData(serializers.Serializer):
    achievement = AlumniAchievementDisplaySerializer()

class AchievementDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AchievementDetailResponseData(allow_null=True)

class AchievementListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AlumniAchievementMinimalSerializer(many=True)

class AchievementListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AchievementListResponseData()

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

class AchievementListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni - Achievements"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="alumni_id", type=int, description="Filter by alumni ID", required=False),
        ],
        responses={200: AchievementListResponseSerializer},
        description="List alumni achievements, optionally filtered by alumni."
    )
    def get(self, request):
        alumni_id = request.query_params.get("alumni_id")
        if alumni_id:
            achievements = AlumniAchievementService.get_achievements_by_alumni(alumni_id)
        else:
            achievements = AlumniAchievement.objects.all().select_related('alumni').order_by('-date_received')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(achievements, request)
        data = wrap_paginated_data(paginator, page, request, AlumniAchievementMinimalSerializer)
        return Response({
            "status": True,
            "message": "Achievements retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Alumni - Achievements"],
        request=AlumniAchievementCreateSerializer,
        responses={201: AchievementCreateResponseSerializer, 400: AchievementCreateResponseSerializer},
        description="Create a new alumni achievement."
    )
    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = AlumniAchievementCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Only allow staff or the alumni owner
            alumni = serializer.validated_data.get('alumni')
            if not (user.is_staff or (alumni.user and user == alumni.user)):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            achievement = serializer.save()
            return Response({
                "status": True,
                "message": "Achievement created.",
                "data": {
                    "id": achievement.id,
                    "alumni": achievement.alumni.id,
                    "title": achievement.title,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AchievementDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, achievement_id):
        return AlumniAchievementService.get_achievement_by_id(achievement_id)

    @extend_schema(
        tags=["Alumni - Achievements"],
        responses={200: AchievementDetailResponseSerializer, 404: AchievementDetailResponseSerializer},
        description="Retrieve a single achievement by ID."
    )
    def get(self, request, achievement_id):
        achievement = self.get_object(achievement_id)
        if not achievement:
            return Response({
                "status": False,
                "message": "Achievement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = AlumniAchievementDisplaySerializer(achievement, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Achievement retrieved.",
            "data": {"achievement": data}
        })

    @extend_schema(
        tags=["Alumni - Achievements"],
        request=AlumniAchievementUpdateSerializer,
        responses={200: AchievementUpdateResponseSerializer, 400: AchievementUpdateResponseSerializer, 403: AchievementUpdateResponseSerializer},
        description="Update an achievement."
    )
    @transaction.atomic
    def put(self, request, achievement_id):
        return self._update(request, achievement_id, partial=False)

    @extend_schema(
        tags=["Alumni - Achievements"],
        request=AlumniAchievementUpdateSerializer,
        responses={200: AchievementUpdateResponseSerializer, 400: AchievementUpdateResponseSerializer, 403: AchievementUpdateResponseSerializer},
        description="Partially update an achievement."
    )
    @transaction.atomic
    def patch(self, request, achievement_id):
        return self._update(request, achievement_id, partial=True)

    def _update(self, request, achievement_id, partial):
        achievement = self.get_object(achievement_id)
        if not achievement:
            return Response({
                "status": False,
                "message": "Achievement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if not (user.is_staff or (achievement.alumni.user and user == achievement.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AlumniAchievementUpdateSerializer(achievement, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AlumniAchievementDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Achievement updated.",
                "data": {"achievement": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Alumni - Achievements"],
        responses={200: AchievementDeleteResponseSerializer, 403: AchievementDeleteResponseSerializer, 404: AchievementDeleteResponseSerializer},
        description="Delete an achievement (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, achievement_id):
        achievement = self.get_object(achievement_id)
        if not achievement:
            return Response({
                "status": False,
                "message": "Achievement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not (user.is_staff or (achievement.alumni.user and user == achievement.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = AlumniAchievementService.delete_achievement(achievement)
        if success:
            return Response({
                "status": True,
                "message": "Achievement deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete achievement.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)