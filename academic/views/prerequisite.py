import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from academic.models import Prerequisite
from academic.serializers.prerequisite import (
    PrerequisiteMinimalSerializer,
    PrerequisiteCreateSerializer,
    PrerequisiteUpdateSerializer,
    PrerequisiteDisplaySerializer,
)
from academic.services.prerequisite import PrerequisiteService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class PrerequisiteCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    subject = serializers.IntegerField()
    required_subject = serializers.IntegerField()

class PrerequisiteCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PrerequisiteCreateResponseData(allow_null=True)

class PrerequisiteUpdateResponseData(serializers.Serializer):
    prerequisite = PrerequisiteDisplaySerializer()

class PrerequisiteUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PrerequisiteUpdateResponseData(allow_null=True)

class PrerequisiteDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class PrerequisiteDetailResponseData(serializers.Serializer):
    prerequisite = PrerequisiteDisplaySerializer()

class PrerequisiteDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PrerequisiteDetailResponseData(allow_null=True)

class PrerequisiteListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PrerequisiteMinimalSerializer(many=True)

class PrerequisiteListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PrerequisiteListResponseData()

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

class PrerequisiteListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Academic - Prerequisites"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject (prerequisite of this subject)", required=False),
            OpenApiParameter(name="required_subject_id", type=int, description="Filter by required subject (subjects that require this subject)", required=False),
        ],
        responses={200: PrerequisiteListResponseSerializer},
        description="List prerequisites, optionally filtered by subject or required subject."
    )
    def get(self, request):
        subject_id = request.query_params.get("subject_id")
        required_subject_id = request.query_params.get("required_subject_id")
        if subject_id:
            prerequisites = PrerequisiteService.get_prerequisites_for_subject(subject_id)
        elif required_subject_id:
            prerequisites = PrerequisiteService.get_subjects_requiring(required_subject_id)
        else:
            prerequisites = Prerequisite.objects.all().select_related('subject', 'required_subject')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(prerequisites, request)
        data = wrap_paginated_data(paginator, page, request, PrerequisiteMinimalSerializer)
        return Response({
            "status": True,
            "message": "Prerequisites retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Academic - Prerequisites"],
        request=PrerequisiteCreateSerializer,
        responses={201: PrerequisiteCreateResponseSerializer, 400: PrerequisiteCreateResponseSerializer},
        description="Create a prerequisite relationship between two subjects."
    )
    @transaction.atomic
    def post(self, request):
        serializer = PrerequisiteCreateSerializer(data=request.data)
        if serializer.is_valid():
            prereq = serializer.save()
            return Response({
                "status": True,
                "message": "Prerequisite created.",
                "data": {
                    "id": prereq.id,
                    "subject": prereq.subject.id,
                    "required_subject": prereq.required_subject.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PrerequisiteDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, prereq_id):
        try:
            return Prerequisite.objects.select_related('subject', 'required_subject').get(id=prereq_id)
        except Prerequisite.DoesNotExist:
            return None

    @extend_schema(
        tags=["Academic - Prerequisites"],
        responses={200: PrerequisiteDetailResponseSerializer, 404: PrerequisiteDetailResponseSerializer},
        description="Retrieve a single prerequisite by ID."
    )
    def get(self, request, prereq_id):
        prereq = self.get_object(prereq_id)
        if not prereq:
            return Response({
                "status": False,
                "message": "Prerequisite not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = PrerequisiteDisplaySerializer(prereq, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Prerequisite retrieved.",
            "data": {"prerequisite": data}
        })

    @extend_schema(
        tags=["Academic - Prerequisites"],
        request=PrerequisiteUpdateSerializer,
        responses={200: PrerequisiteUpdateResponseSerializer, 400: PrerequisiteUpdateResponseSerializer, 403: PrerequisiteUpdateResponseSerializer},
        description="Update a prerequisite (e.g., make optional)."
    )
    @transaction.atomic
    def put(self, request, prereq_id):
        return self._update(request, prereq_id, partial=False)

    @extend_schema(
        tags=["Academic - Prerequisites"],
        request=PrerequisiteUpdateSerializer,
        responses={200: PrerequisiteUpdateResponseSerializer, 400: PrerequisiteUpdateResponseSerializer, 403: PrerequisiteUpdateResponseSerializer},
        description="Partially update a prerequisite."
    )
    @transaction.atomic
    def patch(self, request, prereq_id):
        return self._update(request, prereq_id, partial=True)

    def _update(self, request, prereq_id, partial):
        prereq = self.get_object(prereq_id)
        if not prereq:
            return Response({
                "status": False,
                "message": "Prerequisite not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = PrerequisiteUpdateSerializer(prereq, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PrerequisiteDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Prerequisite updated.",
                "data": {"prerequisite": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Academic - Prerequisites"],
        responses={200: PrerequisiteDeleteResponseSerializer, 403: PrerequisiteDeleteResponseSerializer, 404: PrerequisiteDeleteResponseSerializer},
        description="Delete a prerequisite (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, prereq_id):
        prereq = self.get_object(prereq_id)
        if not prereq:
            return Response({
                "status": False,
                "message": "Prerequisite not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = PrerequisiteService.remove_prerequisite(prereq)
        if success:
            return Response({
                "status": True,
                "message": "Prerequisite deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete prerequisite.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PrerequisiteCheckView(APIView):
    permission_classes = [IsAuthenticated]

    class CheckSerializer(serializers.Serializer):
        completed_subject_ids = serializers.ListField(child=serializers.IntegerField())

    @extend_schema(
        tags=["Academic - Prerequisites"],
        request=CheckSerializer,
        responses={200: serializers.Serializer, 400: serializers.Serializer},
        description="Check if a student has completed all required prerequisites for a given subject."
    )
    def post(self, request, subject_id):
        from academic.models import Subject
        subject = get_object_or_404(Subject, id=subject_id)
        serializer = self.CheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        completed = serializer.validated_data['completed_subject_ids']
        meets = PrerequisiteService.check_prerequisites(subject, completed)
        return Response({
            "status": True,
            "message": "Prerequisite check completed.",
            "data": {"meets_prerequisites": meets}
        })