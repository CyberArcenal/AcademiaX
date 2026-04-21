import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import serializers

from academic.models import Subject
from academic.serializers.subject import (
    SubjectMinimalSerializer,
    SubjectCreateSerializer,
    SubjectUpdateSerializer,
    SubjectDisplaySerializer,
)
from academic.services.subject import SubjectService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers for consistent documentation
# ----------------------------------------------------------------------

class SubjectCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()

class SubjectCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectCreateResponseData(allow_null=True)

class SubjectUpdateResponseData(serializers.Serializer):
    subject = SubjectDisplaySerializer()

class SubjectUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectUpdateResponseData(allow_null=True)

class SubjectDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class SubjectDetailResponseData(serializers.Serializer):
    subject = SubjectDisplaySerializer()

class SubjectDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectDetailResponseData(allow_null=True)

class SubjectListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SubjectMinimalSerializer(many=True)

class SubjectListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectListResponseData()

class SubjectSearchResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SubjectMinimalSerializer(many=True)

class SubjectSearchResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectSearchResponseData()

# Helper
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

class SubjectListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Academic - Subjects"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: SubjectListResponseSerializer},
        description="List subjects (active only by default)."
    )
    def get(self, request):
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        subjects = SubjectService.get_all_subjects(active_only=active_only)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(subjects, request)
        data = wrap_paginated_data(paginator, page, request, SubjectMinimalSerializer)
        return Response({
            "status": True,
            "message": "Subjects retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Academic - Subjects"],
        request=SubjectCreateSerializer,
        responses={201: SubjectCreateResponseSerializer, 400: SubjectCreateResponseSerializer},
        description="Create a new subject."
    )
    @transaction.atomic
    def post(self, request):
        serializer = SubjectCreateSerializer(data=request.data)
        if serializer.is_valid():
            subject = serializer.save()
            return Response({
                "status": True,
                "message": "Subject created successfully.",
                "data": {"id": subject.id, "code": subject.code}
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SubjectDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, subject_id):
        return SubjectService.get_subject_by_id(subject_id)

    @extend_schema(
        tags=["Academic - Subjects"],
        responses={200: SubjectDetailResponseSerializer, 404: SubjectDetailResponseSerializer},
        description="Retrieve a single subject by ID."
    )
    def get(self, request, subject_id):
        subject = self.get_object(subject_id)
        if not subject:
            return Response({
                "status": False,
                "message": "Subject not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = SubjectDisplaySerializer(subject, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Subject retrieved.",
            "data": {"subject": data}
        })

    @extend_schema(
        tags=["Academic - Subjects"],
        request=SubjectUpdateSerializer,
        responses={200: SubjectUpdateResponseSerializer, 400: SubjectUpdateResponseSerializer, 403: SubjectUpdateResponseSerializer},
        description="Update a subject (full update)."
    )
    @transaction.atomic
    def put(self, request, subject_id):
        return self._update(request, subject_id, partial=False)

    @extend_schema(
        tags=["Academic - Subjects"],
        request=SubjectUpdateSerializer,
        responses={200: SubjectUpdateResponseSerializer, 400: SubjectUpdateResponseSerializer, 403: SubjectUpdateResponseSerializer},
        description="Partially update a subject."
    )
    @transaction.atomic
    def patch(self, request, subject_id):
        return self._update(request, subject_id, partial=True)

    def _update(self, request, subject_id, partial):
        subject = self.get_object(subject_id)
        if not subject:
            return Response({
                "status": False,
                "message": "Subject not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Only admin or staff can update – adjust as needed
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "You do not have permission to update this subject.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = SubjectUpdateSerializer(subject, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = SubjectDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Subject updated successfully.",
                "data": {"subject": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Academic - Subjects"],
        parameters=[
            OpenApiParameter(name="hard", type=bool, description="Permanently delete", required=False),
        ],
        responses={200: SubjectDeleteResponseSerializer, 403: SubjectDeleteResponseSerializer, 404: SubjectDeleteResponseSerializer},
        description="Delete a subject (soft delete by default)."
    )
    @transaction.atomic
    def delete(self, request, subject_id):
        subject = self.get_object(subject_id)
        if not subject:
            return Response({
                "status": False,
                "message": "Subject not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "You do not have permission to delete this subject.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        hard = request.query_params.get("hard", "false").lower() == "true"
        success = SubjectService.delete_subject(subject, soft_delete=not hard)
        if success:
            return Response({
                "status": True,
                "message": "Subject deleted successfully." + (" (permanent)" if hard else ""),
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete subject.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubjectSearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Academic - Subjects"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: SubjectSearchResponseSerializer},
        description="Search subjects by code or name."
    )
    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter is required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        subjects = SubjectService.search_subjects(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(subjects, request)
        data = wrap_paginated_data(paginator, page, request, SubjectMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })