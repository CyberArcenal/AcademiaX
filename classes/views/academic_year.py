import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from classes.models import AcademicYear
from classes.serializers.academic_year import (
    AcademicYearMinimalSerializer,
    AcademicYearCreateSerializer,
    AcademicYearUpdateSerializer,
    AcademicYearDisplaySerializer,
)
from classes.services.academic_year import AcademicYearService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_academic_year(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AcademicYearCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class AcademicYearCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AcademicYearCreateResponseData(allow_null=True)

class AcademicYearUpdateResponseData(serializers.Serializer):
    academic_year = AcademicYearDisplaySerializer()

class AcademicYearUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AcademicYearUpdateResponseData(allow_null=True)

class AcademicYearDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AcademicYearDetailResponseData(serializers.Serializer):
    academic_year = AcademicYearDisplaySerializer()

class AcademicYearDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AcademicYearDetailResponseData(allow_null=True)

class AcademicYearListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AcademicYearMinimalSerializer(many=True)

class AcademicYearListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AcademicYearListResponseData()

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

class AcademicYearListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Academic Years"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="current_only", type=bool, description="Only current academic year", required=False),
        ],
        responses={200: AcademicYearListResponseSerializer},
        description="List academic years."
    )
    def get(self, request):
        current_only = request.query_params.get("current_only", "false").lower() == "true"
        if current_only:
            years = [AcademicYearService.get_current_academic_year()] if AcademicYearService.get_current_academic_year() else []
        else:
            years = AcademicYearService.get_all_academic_years()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(years, request)
        data = wrap_paginated_data(paginator, page, request, AcademicYearMinimalSerializer)
        return Response({
            "status": True,
            "message": "Academic years retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Classes - Academic Years"],
        request=AcademicYearCreateSerializer,
        responses={201: AcademicYearCreateResponseSerializer, 400: AcademicYearCreateResponseSerializer, 403: AcademicYearCreateResponseSerializer},
        description="Create a new academic year (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_academic_year(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = AcademicYearCreateSerializer(data=request.data)
        if serializer.is_valid():
            year = serializer.save()
            return Response({
                "status": True,
                "message": "Academic year created.",
                "data": {"id": year.id, "name": year.name}
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AcademicYearDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, year_id):
        return AcademicYearService.get_academic_year_by_id(year_id)

    @extend_schema(
        tags=["Classes - Academic Years"],
        responses={200: AcademicYearDetailResponseSerializer, 404: AcademicYearDetailResponseSerializer},
        description="Retrieve a single academic year by ID."
    )
    def get(self, request, year_id):
        year = self.get_object(year_id)
        if not year:
            return Response({
                "status": False,
                "message": "Academic year not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = AcademicYearDisplaySerializer(year, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Academic year retrieved.",
            "data": {"academic_year": data}
        })

    @extend_schema(
        tags=["Classes - Academic Years"],
        request=AcademicYearUpdateSerializer,
        responses={200: AcademicYearUpdateResponseSerializer, 400: AcademicYearUpdateResponseSerializer, 403: AcademicYearUpdateResponseSerializer},
        description="Update an academic year (admin only)."
    )
    @transaction.atomic
    def put(self, request, year_id):
        return self._update(request, year_id, partial=False)

    @extend_schema(
        tags=["Classes - Academic Years"],
        request=AcademicYearUpdateSerializer,
        responses={200: AcademicYearUpdateResponseSerializer, 400: AcademicYearUpdateResponseSerializer, 403: AcademicYearUpdateResponseSerializer},
        description="Partially update an academic year."
    )
    @transaction.atomic
    def patch(self, request, year_id):
        return self._update(request, year_id, partial=True)

    def _update(self, request, year_id, partial):
        if not can_manage_academic_year(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        year = self.get_object(year_id)
        if not year:
            return Response({
                "status": False,
                "message": "Academic year not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = AcademicYearUpdateSerializer(year, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AcademicYearDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Academic year updated.",
                "data": {"academic_year": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Classes - Academic Years"],
        responses={200: AcademicYearDeleteResponseSerializer, 403: AcademicYearDeleteResponseSerializer, 404: AcademicYearDeleteResponseSerializer},
        description="Delete an academic year (admin only)."
    )
    @transaction.atomic
    def delete(self, request, year_id):
        if not can_manage_academic_year(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        year = self.get_object(year_id)
        if not year:
            return Response({
                "status": False,
                "message": "Academic year not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = AcademicYearService.delete_academic_year(year)
        if success:
            return Response({
                "status": True,
                "message": "Academic year deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete academic year.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcademicYearSetCurrentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Classes - Academic Years"],
        responses={200: AcademicYearDetailResponseSerializer, 403: AcademicYearDetailResponseSerializer, 404: AcademicYearDetailResponseSerializer},
        description="Set an academic year as current (admin only)."
    )
    @transaction.atomic
    def post(self, request, year_id):
        if not can_manage_academic_year(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        year = AcademicYearService.get_academic_year_by_id(year_id)
        if not year:
            return Response({
                "status": False,
                "message": "Academic year not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = AcademicYearService.set_current(year)
        data = AcademicYearDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Current academic year updated.",
            "data": {"academic_year": data}
        })