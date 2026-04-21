import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from alumni.models import Alumni
from alumni.serializers.alumni import (
    AlumniMinimalSerializer,
    AlumniCreateSerializer,
    AlumniUpdateSerializer,
    AlumniDisplaySerializer,
)
from alumni.services.alumni import AlumniService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AlumniCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student_id = serializers.IntegerField(allow_null=True)
    user_id = serializers.IntegerField(allow_null=True)

class AlumniCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniCreateResponseData(allow_null=True)

class AlumniUpdateResponseData(serializers.Serializer):
    alumni = AlumniDisplaySerializer()

class AlumniUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniUpdateResponseData(allow_null=True)

class AlumniDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AlumniDetailResponseData(serializers.Serializer):
    alumni = AlumniDisplaySerializer()

class AlumniDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniDetailResponseData(allow_null=True)

class AlumniListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AlumniMinimalSerializer(many=True)

class AlumniListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AlumniListResponseData()

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

class AlumniListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
            OpenApiParameter(name="graduation_year", type=int, required=False),
        ],
        responses={200: AlumniListResponseSerializer},
        description="List alumni records, optionally filtered by graduation year or active status."
    )
    def get(self, request):
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        graduation_year = request.query_params.get("graduation_year")
        alumni = Alumni.objects.filter(is_active=active_only) if active_only else Alumni.objects.all()
        if graduation_year:
            alumni = alumni.filter(graduation_year=graduation_year)
        alumni = alumni.order_by('-graduation_year')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(alumni, request)
        data = wrap_paginated_data(paginator, page, request, AlumniMinimalSerializer)
        return Response({
            "status": True,
            "message": "Alumni retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Alumni"],
        request=AlumniCreateSerializer,
        responses={201: AlumniCreateResponseSerializer, 400: AlumniCreateResponseSerializer},
        description="Create a new alumni record."
    )
    @transaction.atomic
    def post(self, request):
        serializer = AlumniCreateSerializer(data=request.data)
        if serializer.is_valid():
            alumni = serializer.save()
            return Response({
                "status": True,
                "message": "Alumni created.",
                "data": {
                    "id": alumni.id,
                    "student_id": alumni.student_id,
                    "user_id": alumni.user_id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AlumniDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, alumni_id):
        return AlumniService.get_alumni_by_id(alumni_id)

    @extend_schema(
        tags=["Alumni"],
        responses={200: AlumniDetailResponseSerializer, 404: AlumniDetailResponseSerializer},
        description="Retrieve a single alumni record by ID."
    )
    def get(self, request, alumni_id):
        alumni = self.get_object(alumni_id)
        if not alumni:
            return Response({
                "status": False,
                "message": "Alumni not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = AlumniDisplaySerializer(alumni, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Alumni retrieved.",
            "data": {"alumni": data}
        })

    @extend_schema(
        tags=["Alumni"],
        request=AlumniUpdateSerializer,
        responses={200: AlumniUpdateResponseSerializer, 400: AlumniUpdateResponseSerializer, 403: AlumniUpdateResponseSerializer},
        description="Update an alumni record."
    )
    @transaction.atomic
    def put(self, request, alumni_id):
        return self._update(request, alumni_id, partial=False)

    @extend_schema(
        tags=["Alumni"],
        request=AlumniUpdateSerializer,
        responses={200: AlumniUpdateResponseSerializer, 400: AlumniUpdateResponseSerializer, 403: AlumniUpdateResponseSerializer},
        description="Partially update an alumni record."
    )
    @transaction.atomic
    def patch(self, request, alumni_id):
        return self._update(request, alumni_id, partial=True)

    def _update(self, request, alumni_id, partial):
        alumni = self.get_object(alumni_id)
        if not alumni:
            return Response({
                "status": False,
                "message": "Alumni not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not (request.user.is_staff or (alumni.user and request.user == alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AlumniUpdateSerializer(alumni, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AlumniDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Alumni updated.",
                "data": {"alumni": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Alumni"],
        parameters=[OpenApiParameter(name="hard", type=bool, required=False)],
        responses={200: AlumniDeleteResponseSerializer, 403: AlumniDeleteResponseSerializer, 404: AlumniDeleteResponseSerializer},
        description="Delete an alumni record (soft delete by default)."
    )
    @transaction.atomic
    def delete(self, request, alumni_id):
        alumni = self.get_object(alumni_id)
        if not alumni:
            return Response({
                "status": False,
                "message": "Alumni not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not (request.user.is_staff or (alumni.user and request.user == alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        hard = request.query_params.get("hard", "false").lower() == "true"
        success = AlumniService.delete_alumni(alumni, soft_delete=not hard)
        if success:
            return Response({
                "status": True,
                "message": "Alumni deleted successfully." + (" (permanent)" if hard else ""),
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete alumni.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlumniSearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: AlumniListResponseSerializer},
        description="Search alumni by name, batch, or city."
    )
    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        alumni = AlumniService.search_alumni(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(alumni, request)
        data = wrap_paginated_data(paginator, page, request, AlumniMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })