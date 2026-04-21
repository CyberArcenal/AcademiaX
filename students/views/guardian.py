import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from students.models import Guardian
from students.serializers.guardian import (
    GuardianMinimalSerializer,
    GuardianCreateSerializer,
    GuardianUpdateSerializer,
    GuardianDisplaySerializer,
)
from students.services.guardian import GuardianService

logger = logging.getLogger(__name__)

def can_view_guardian(user, guardian):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return guardian.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        # Parent can see their own record if it matches
        return guardian.id == user.parent_profile.id if hasattr(user, 'parent_profile') else False
    return False

def can_manage_guardian(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class GuardianCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    relationship = serializers.CharField()

class GuardianCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GuardianCreateResponseData(allow_null=True)

class GuardianUpdateResponseData(serializers.Serializer):
    guardian = GuardianDisplaySerializer()

class GuardianUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GuardianUpdateResponseData(allow_null=True)

class GuardianDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class GuardianDetailResponseData(serializers.Serializer):
    guardian = GuardianDisplaySerializer()

class GuardianDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GuardianDetailResponseData(allow_null=True)

class GuardianListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = GuardianMinimalSerializer(many=True)

class GuardianListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GuardianListResponseData()

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

class GuardianListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Students - Guardians"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
        ],
        responses={200: GuardianListResponseSerializer},
        description="List guardians (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")

        if user.is_staff or can_manage_guardian(user):
            queryset = Guardian.objects.all().select_related('student')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = Guardian.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                queryset = Guardian.objects.filter(id=user.parent_profile.id)
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
        data = wrap_paginated_data(paginator, page, request, GuardianMinimalSerializer)
        return Response({
            "status": True,
            "message": "Guardians retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Students - Guardians"],
        request=GuardianCreateSerializer,
        responses={201: GuardianCreateResponseSerializer, 400: GuardianCreateResponseSerializer, 403: GuardianCreateResponseSerializer},
        description="Create a guardian (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_guardian(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = GuardianCreateSerializer(data=request.data)
        if serializer.is_valid():
            guardian = serializer.save()
            return Response({
                "status": True,
                "message": "Guardian created.",
                "data": {
                    "id": guardian.id,
                    "student": guardian.student.id,
                    "first_name": guardian.first_name,
                    "last_name": guardian.last_name,
                    "relationship": guardian.relationship,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GuardianDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, guardian_id):
        try:
            return Guardian.objects.select_related('student').get(id=guardian_id)
        except Guardian.DoesNotExist:
            return None

    @extend_schema(
        tags=["Students - Guardians"],
        responses={200: GuardianDetailResponseSerializer, 404: GuardianDetailResponseSerializer, 403: GuardianDetailResponseSerializer},
        description="Retrieve a single guardian by ID."
    )
    def get(self, request, guardian_id):
        guardian = self.get_object(guardian_id)
        if not guardian:
            return Response({
                "status": False,
                "message": "Guardian not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_guardian(request.user, guardian):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = GuardianDisplaySerializer(guardian, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Guardian retrieved.",
            "data": {"guardian": data}
        })

    @extend_schema(
        tags=["Students - Guardians"],
        request=GuardianUpdateSerializer,
        responses={200: GuardianUpdateResponseSerializer, 400: GuardianUpdateResponseSerializer, 403: GuardianUpdateResponseSerializer},
        description="Update a guardian (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, guardian_id):
        return self._update(request, guardian_id, partial=False)

    @extend_schema(
        tags=["Students - Guardians"],
        request=GuardianUpdateSerializer,
        responses={200: GuardianUpdateResponseSerializer, 400: GuardianUpdateResponseSerializer, 403: GuardianUpdateResponseSerializer},
        description="Partially update a guardian."
    )
    @transaction.atomic
    def patch(self, request, guardian_id):
        return self._update(request, guardian_id, partial=True)

    def _update(self, request, guardian_id, partial):
        if not can_manage_guardian(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        guardian = self.get_object(guardian_id)
        if not guardian:
            return Response({
                "status": False,
                "message": "Guardian not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = GuardianUpdateSerializer(guardian, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = GuardianDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Guardian updated.",
                "data": {"guardian": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Students - Guardians"],
        responses={200: GuardianDeleteResponseSerializer, 403: GuardianDeleteResponseSerializer, 404: GuardianDeleteResponseSerializer},
        description="Delete a guardian (admin only)."
    )
    @transaction.atomic
    def delete(self, request, guardian_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        guardian = self.get_object(guardian_id)
        if not guardian:
            return Response({
                "status": False,
                "message": "Guardian not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = GuardianService.delete_guardian(guardian)
        if success:
            return Response({
                "status": True,
                "message": "Guardian deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete guardian.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)