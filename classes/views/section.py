import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from classes.models import Section
from classes.serializers.section import (
    SectionMinimalSerializer,
    SectionCreateSerializer,
    SectionUpdateSerializer,
    SectionDisplaySerializer,
)
from classes.services.section import SectionService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_section(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class SectionCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    grade_level = serializers.IntegerField()

class SectionCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SectionCreateResponseData(allow_null=True)

class SectionUpdateResponseData(serializers.Serializer):
    section = SectionDisplaySerializer()

class SectionUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SectionUpdateResponseData(allow_null=True)

class SectionDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class SectionDetailResponseData(serializers.Serializer):
    section = SectionDisplaySerializer()

class SectionDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SectionDetailResponseData(allow_null=True)

class SectionListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SectionMinimalSerializer(many=True)

class SectionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SectionListResponseData()

class SectionAvailabilityResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    capacity = serializers.IntegerField()
    current_enrollment = serializers.IntegerField()
    remaining = serializers.IntegerField()

class SectionAvailabilityListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.ListField(child=SectionAvailabilityResponseData())

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

class SectionListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Sections"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="grade_level_id", type=int, description="Filter by grade level ID", required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year ID", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active sections", required=False),
        ],
        responses={200: SectionListResponseSerializer},
        description="List sections, optionally filtered by grade level and/or academic year."
    )
    def get(self, request):
        grade_level_id = request.query_params.get("grade_level_id")
        academic_year_id = request.query_params.get("academic_year_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        queryset = Section.objects.all().select_related('grade_level', 'academic_year', 'homeroom_teacher', 'classroom')
        if grade_level_id:
            queryset = queryset.filter(grade_level_id=grade_level_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if active_only:
            queryset = queryset.filter(is_active=True)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, SectionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Sections retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Classes - Sections"],
        request=SectionCreateSerializer,
        responses={201: SectionCreateResponseSerializer, 400: SectionCreateResponseSerializer, 403: SectionCreateResponseSerializer},
        description="Create a new section (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_section(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = SectionCreateSerializer(data=request.data)
        if serializer.is_valid():
            section = serializer.save()
            return Response({
                "status": True,
                "message": "Section created.",
                "data": {
                    "id": section.id,
                    "name": section.name,
                    "grade_level": section.grade_level.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SectionDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, section_id):
        return SectionService.get_section_by_id(section_id)

    @extend_schema(
        tags=["Classes - Sections"],
        responses={200: SectionDetailResponseSerializer, 404: SectionDetailResponseSerializer},
        description="Retrieve a single section by ID."
    )
    def get(self, request, section_id):
        section = self.get_object(section_id)
        if not section:
            return Response({
                "status": False,
                "message": "Section not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = SectionDisplaySerializer(section, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Section retrieved.",
            "data": {"section": data}
        })

    @extend_schema(
        tags=["Classes - Sections"],
        request=SectionUpdateSerializer,
        responses={200: SectionUpdateResponseSerializer, 400: SectionUpdateResponseSerializer, 403: SectionUpdateResponseSerializer},
        description="Update a section (admin only)."
    )
    @transaction.atomic
    def put(self, request, section_id):
        return self._update(request, section_id, partial=False)

    @extend_schema(
        tags=["Classes - Sections"],
        request=SectionUpdateSerializer,
        responses={200: SectionUpdateResponseSerializer, 400: SectionUpdateResponseSerializer, 403: SectionUpdateResponseSerializer},
        description="Partially update a section."
    )
    @transaction.atomic
    def patch(self, request, section_id):
        return self._update(request, section_id, partial=True)

    def _update(self, request, section_id, partial):
        if not can_manage_section(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        section = self.get_object(section_id)
        if not section:
            return Response({
                "status": False,
                "message": "Section not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = SectionUpdateSerializer(section, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = SectionDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Section updated.",
                "data": {"section": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Classes - Sections"],
        responses={200: SectionDeleteResponseSerializer, 403: SectionDeleteResponseSerializer, 404: SectionDeleteResponseSerializer},
        description="Delete a section (admin only)."
    )
    @transaction.atomic
    def delete(self, request, section_id):
        if not can_manage_section(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        section = self.get_object(section_id)
        if not section:
            return Response({
                "status": False,
                "message": "Section not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = SectionService.delete_section(section)
        if success:
            return Response({
                "status": True,
                "message": "Section deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete section.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SectionAvailabilityView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Sections"],
        parameters=[
            OpenApiParameter(name="grade_level_id", type=int, description="Grade level ID", required=True),
            OpenApiParameter(name="academic_year_id", type=int, description="Academic year ID", required=True),
        ],
        responses={200: SectionAvailabilityListResponseSerializer},
        description="Get sections with remaining capacity for a given grade level and academic year."
    )
    def get(self, request):
        grade_level_id = request.query_params.get("grade_level_id")
        academic_year_id = request.query_params.get("academic_year_id")
        if not grade_level_id or not academic_year_id:
            return Response({
                "status": False,
                "message": "grade_level_id and academic_year_id parameters required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        sections = SectionService.get_sections_with_availability(grade_level_id, academic_year_id)
        return Response({
            "status": True,
            "message": "Section availability retrieved.",
            "data": sections
        })


class SectionUpdateEnrollmentCountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Classes - Sections"],
        responses={200: SectionDetailResponseSerializer, 403: SectionDetailResponseSerializer, 404: SectionDetailResponseSerializer},
        description="Recalculate and update the current enrollment count for a section (admin only)."
    )
    @transaction.atomic
    def post(self, request, section_id):
        if not can_manage_section(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        section = SectionService.get_section_by_id(section_id)
        if not section:
            return Response({
                "status": False,
                "message": "Section not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = SectionService.update_enrollment_count(section)
        data = SectionDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Enrollment count updated.",
            "data": {"section": data}
        })