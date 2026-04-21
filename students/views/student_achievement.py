import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from students.models import StudentAchievement
from students.serializers.student_achievement import (
    StudentAchievementMinimalSerializer,
    StudentAchievementCreateSerializer,
    StudentAchievementUpdateSerializer,
    StudentAchievementDisplaySerializer,
)
from students.services.student_achievement import StudentAchievementService

logger = logging.getLogger(__name__)

def can_view_achievement(user, achievement):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return achievement.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return achievement.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        # Teachers can see achievements of students they teach
        teacher = user.teacher_profile
        sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
        from enrollments.models import Enrollment
        student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
        return achievement.student.id in student_ids
    return False

def can_manage_achievement(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AchievementCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    title = serializers.CharField()
    level = serializers.CharField()

class AchievementCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AchievementCreateResponseData(allow_null=True)

class AchievementUpdateResponseData(serializers.Serializer):
    achievement = StudentAchievementDisplaySerializer()

class AchievementUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AchievementUpdateResponseData(allow_null=True)

class AchievementDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AchievementDetailResponseData(serializers.Serializer):
    achievement = StudentAchievementDisplaySerializer()

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
    results = StudentAchievementMinimalSerializer(many=True)

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

class StudentAchievementListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Students - Achievements"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="level", type=str, description="Filter by achievement level", required=False),
        ],
        responses={200: AchievementListResponseSerializer},
        description="List student achievements (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        level_filter = request.query_params.get("level")

        if user.is_staff or can_manage_achievement(user):
            queryset = StudentAchievement.objects.all().select_related('student')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = StudentAchievement.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = StudentAchievement.objects.filter(student_id__in=child_ids)
            elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                teacher = user.teacher_profile
                sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                from enrollments.models import Enrollment
                student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
                queryset = StudentAchievement.objects.filter(student_id__in=student_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if level_filter:
            queryset = queryset.filter(level=level_filter)

        queryset = queryset.order_by('-date_awarded')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, StudentAchievementMinimalSerializer)
        return Response({
            "status": True,
            "message": "Student achievements retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Students - Achievements"],
        request=StudentAchievementCreateSerializer,
        responses={201: AchievementCreateResponseSerializer, 400: AchievementCreateResponseSerializer, 403: AchievementCreateResponseSerializer},
        description="Create a student achievement (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_achievement(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = StudentAchievementCreateSerializer(data=request.data)
        if serializer.is_valid():
            achievement = serializer.save()
            return Response({
                "status": True,
                "message": "Achievement created.",
                "data": {
                    "id": achievement.id,
                    "student": achievement.student.id,
                    "title": achievement.title,
                    "level": achievement.level,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentAchievementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, achievement_id):
        try:
            return StudentAchievement.objects.select_related('student').get(id=achievement_id)
        except StudentAchievement.DoesNotExist:
            return None

    @extend_schema(
        tags=["Students - Achievements"],
        responses={200: AchievementDetailResponseSerializer, 404: AchievementDetailResponseSerializer, 403: AchievementDetailResponseSerializer},
        description="Retrieve a single student achievement by ID."
    )
    def get(self, request, achievement_id):
        achievement = self.get_object(achievement_id)
        if not achievement:
            return Response({
                "status": False,
                "message": "Achievement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_achievement(request.user, achievement):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = StudentAchievementDisplaySerializer(achievement, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Achievement retrieved.",
            "data": {"achievement": data}
        })

    @extend_schema(
        tags=["Students - Achievements"],
        request=StudentAchievementUpdateSerializer,
        responses={200: AchievementUpdateResponseSerializer, 400: AchievementUpdateResponseSerializer, 403: AchievementUpdateResponseSerializer},
        description="Update a student achievement (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, achievement_id):
        return self._update(request, achievement_id, partial=False)

    @extend_schema(
        tags=["Students - Achievements"],
        request=StudentAchievementUpdateSerializer,
        responses={200: AchievementUpdateResponseSerializer, 400: AchievementUpdateResponseSerializer, 403: AchievementUpdateResponseSerializer},
        description="Partially update a student achievement."
    )
    @transaction.atomic
    def patch(self, request, achievement_id):
        return self._update(request, achievement_id, partial=True)

    def _update(self, request, achievement_id, partial):
        if not can_manage_achievement(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        achievement = self.get_object(achievement_id)
        if not achievement:
            return Response({
                "status": False,
                "message": "Achievement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentAchievementUpdateSerializer(achievement, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = StudentAchievementDisplaySerializer(updated, context={"request": request}).data
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
        tags=["Students - Achievements"],
        responses={200: AchievementDeleteResponseSerializer, 403: AchievementDeleteResponseSerializer, 404: AchievementDeleteResponseSerializer},
        description="Delete a student achievement (admin only)."
    )
    @transaction.atomic
    def delete(self, request, achievement_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        achievement = self.get_object(achievement_id)
        if not achievement:
            return Response({
                "status": False,
                "message": "Achievement not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = StudentAchievementService.delete_achievement(achievement)
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