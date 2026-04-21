import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from grades.models import GradeComponent
from grades.serializers.grade_component import (
    GradeComponentMinimalSerializer,
    GradeComponentCreateSerializer,
    GradeComponentUpdateSerializer,
    GradeComponentDisplaySerializer,
)
from grades.services.grade_component import GradeComponentService

logger = logging.getLogger(__name__)

def can_manage_grade_component(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'TEACHER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class GradeComponentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subject = serializers.IntegerField()
    weight = serializers.DecimalField(max_digits=5, decimal_places=2)

class GradeComponentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeComponentCreateResponseData(allow_null=True)

class GradeComponentUpdateResponseData(serializers.Serializer):
    component = GradeComponentDisplaySerializer()

class GradeComponentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeComponentUpdateResponseData(allow_null=True)

class GradeComponentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class GradeComponentDetailResponseData(serializers.Serializer):
    component = GradeComponentDisplaySerializer()

class GradeComponentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeComponentDetailResponseData(allow_null=True)

class GradeComponentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = GradeComponentMinimalSerializer(many=True)

class GradeComponentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeComponentListResponseData()

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

class GradeComponentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Components"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject ID", required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year ID", required=False),
            OpenApiParameter(name="grade_level_id", type=int, description="Filter by grade level ID", required=False),
        ],
        responses={200: GradeComponentListResponseSerializer},
        description="List grade components (teachers/admins only)."
    )
    def get(self, request):
        if not can_manage_grade_component(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        subject_id = request.query_params.get("subject_id")
        academic_year_id = request.query_params.get("academic_year_id")
        grade_level_id = request.query_params.get("grade_level_id")
        queryset = GradeComponent.objects.all().select_related('subject', 'academic_year', 'grade_level')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if grade_level_id:
            queryset = queryset.filter(grade_level_id=grade_level_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, GradeComponentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Grade components retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Grades - Components"],
        request=GradeComponentCreateSerializer,
        responses={201: GradeComponentCreateResponseSerializer, 400: GradeComponentCreateResponseSerializer, 403: GradeComponentCreateResponseSerializer},
        description="Create a grade component (teacher/admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_grade_component(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = GradeComponentCreateSerializer(data=request.data)
        if serializer.is_valid():
            component = serializer.save()
            return Response({
                "status": True,
                "message": "Grade component created.",
                "data": {
                    "id": component.id,
                    "name": component.name,
                    "subject": component.subject.id,
                    "weight": component.weight,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GradeComponentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, component_id):
        try:
            return GradeComponent.objects.select_related('subject', 'academic_year', 'grade_level').get(id=component_id)
        except GradeComponent.DoesNotExist:
            return None

    @extend_schema(
        tags=["Grades - Components"],
        responses={200: GradeComponentDetailResponseSerializer, 404: GradeComponentDetailResponseSerializer, 403: GradeComponentDetailResponseSerializer},
        description="Retrieve a single grade component by ID."
    )
    def get(self, request, component_id):
        if not can_manage_grade_component(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        component = self.get_object(component_id)
        if not component:
            return Response({
                "status": False,
                "message": "Grade component not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = GradeComponentDisplaySerializer(component, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Grade component retrieved.",
            "data": {"component": data}
        })

    @extend_schema(
        tags=["Grades - Components"],
        request=GradeComponentUpdateSerializer,
        responses={200: GradeComponentUpdateResponseSerializer, 400: GradeComponentUpdateResponseSerializer, 403: GradeComponentUpdateResponseSerializer},
        description="Update a grade component (teacher/admin only)."
    )
    @transaction.atomic
    def put(self, request, component_id):
        return self._update(request, component_id, partial=False)

    @extend_schema(
        tags=["Grades - Components"],
        request=GradeComponentUpdateSerializer,
        responses={200: GradeComponentUpdateResponseSerializer, 400: GradeComponentUpdateResponseSerializer, 403: GradeComponentUpdateResponseSerializer},
        description="Partially update a grade component."
    )
    @transaction.atomic
    def patch(self, request, component_id):
        return self._update(request, component_id, partial=True)

    def _update(self, request, component_id, partial):
        if not can_manage_grade_component(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        component = self.get_object(component_id)
        if not component:
            return Response({
                "status": False,
                "message": "Grade component not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = GradeComponentUpdateSerializer(component, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = GradeComponentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Grade component updated.",
                "data": {"component": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Grades - Components"],
        responses={200: GradeComponentDeleteResponseSerializer, 403: GradeComponentDeleteResponseSerializer, 404: GradeComponentDeleteResponseSerializer},
        description="Delete a grade component (admin only)."
    )
    @transaction.atomic
    def delete(self, request, component_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        component = self.get_object(component_id)
        if not component:
            return Response({
                "status": False,
                "message": "Grade component not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = GradeComponentService.delete_component(component)
        if success:
            return Response({
                "status": True,
                "message": "Grade component deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete grade component.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GradeComponentValidateWeightsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Components"],
        parameters=[
            OpenApiParameter(name="subject_id", type=int, description="Subject ID", required=True),
            OpenApiParameter(name="academic_year_id", type=int, description="Academic year ID", required=True),
            OpenApiParameter(name="grade_level_id", type=int, description="Grade level ID", required=True),
        ],
        responses={200: serializers.Serializer, 403: serializers.Serializer},
        description="Validate that grade components sum to 100% for a given subject/year/level."
    )
    def get(self, request):
        if not can_manage_grade_component(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        subject_id = request.query_params.get("subject_id")
        academic_year_id = request.query_params.get("academic_year_id")
        grade_level_id = request.query_params.get("grade_level_id")
        if not all([subject_id, academic_year_id, grade_level_id]):
            return Response({
                "status": False,
                "message": "subject_id, academic_year_id, and grade_level_id are required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        valid = GradeComponentService.validate_weights(subject_id, academic_year_id, grade_level_id)
        return Response({
            "status": True,
            "message": "Validation completed.",
            "data": {"valid": valid}
        })