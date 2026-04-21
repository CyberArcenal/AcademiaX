import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from academic.models import LearningOutcome
from academic.serializers.learning_outcome import (
    LearningOutcomeMinimalSerializer,
    LearningOutcomeCreateSerializer,
    LearningOutcomeUpdateSerializer,
    LearningOutcomeDisplaySerializer,
)
from academic.services.learning_outcome import LearningOutcomeService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class LearningOutcomeCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    subject = serializers.IntegerField()

class LearningOutcomeCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LearningOutcomeCreateResponseData(allow_null=True)

class LearningOutcomeUpdateResponseData(serializers.Serializer):
    learning_outcome = LearningOutcomeDisplaySerializer()

class LearningOutcomeUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LearningOutcomeUpdateResponseData(allow_null=True)

class LearningOutcomeDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class LearningOutcomeDetailResponseData(serializers.Serializer):
    learning_outcome = LearningOutcomeDisplaySerializer()

class LearningOutcomeDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LearningOutcomeDetailResponseData(allow_null=True)

class LearningOutcomeListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = LearningOutcomeMinimalSerializer(many=True)

class LearningOutcomeListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = LearningOutcomeListResponseData()

class LearningOutcomeReorderResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

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

class LearningOutcomeListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Academic - Learning Outcomes"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject ID", required=False),
        ],
        responses={200: LearningOutcomeListResponseSerializer},
        description="List learning outcomes, optionally filtered by subject."
    )
    def get(self, request):
        subject_id = request.query_params.get("subject_id")
        if subject_id:
            outcomes = LearningOutcomeService.get_outcomes_by_subject(subject_id)
        else:
            outcomes = LearningOutcome.objects.all().select_related('subject')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(outcomes, request)
        data = wrap_paginated_data(paginator, page, request, LearningOutcomeMinimalSerializer)
        return Response({
            "status": True,
            "message": "Learning outcomes retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Academic - Learning Outcomes"],
        request=LearningOutcomeCreateSerializer,
        responses={201: LearningOutcomeCreateResponseSerializer, 400: LearningOutcomeCreateResponseSerializer},
        description="Create a new learning outcome."
    )
    @transaction.atomic
    def post(self, request):
        serializer = LearningOutcomeCreateSerializer(data=request.data)
        if serializer.is_valid():
            outcome = serializer.save()
            return Response({
                "status": True,
                "message": "Learning outcome created.",
                "data": {
                    "id": outcome.id,
                    "code": outcome.code,
                    "subject": outcome.subject.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LearningOutcomeDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, outcome_id):
        return LearningOutcomeService.get_outcome_by_id(outcome_id)

    @extend_schema(
        tags=["Academic - Learning Outcomes"],
        responses={200: LearningOutcomeDetailResponseSerializer, 404: LearningOutcomeDetailResponseSerializer},
        description="Retrieve a single learning outcome by ID."
    )
    def get(self, request, outcome_id):
        outcome = self.get_object(outcome_id)
        if not outcome:
            return Response({
                "status": False,
                "message": "Learning outcome not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = LearningOutcomeDisplaySerializer(outcome, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Learning outcome retrieved.",
            "data": {"learning_outcome": data}
        })

    @extend_schema(
        tags=["Academic - Learning Outcomes"],
        request=LearningOutcomeUpdateSerializer,
        responses={200: LearningOutcomeUpdateResponseSerializer, 400: LearningOutcomeUpdateResponseSerializer, 403: LearningOutcomeUpdateResponseSerializer},
        description="Update a learning outcome."
    )
    @transaction.atomic
    def put(self, request, outcome_id):
        return self._update(request, outcome_id, partial=False)

    @extend_schema(
        tags=["Academic - Learning Outcomes"],
        request=LearningOutcomeUpdateSerializer,
        responses={200: LearningOutcomeUpdateResponseSerializer, 400: LearningOutcomeUpdateResponseSerializer, 403: LearningOutcomeUpdateResponseSerializer},
        description="Partially update a learning outcome."
    )
    @transaction.atomic
    def patch(self, request, outcome_id):
        return self._update(request, outcome_id, partial=True)

    def _update(self, request, outcome_id, partial):
        outcome = self.get_object(outcome_id)
        if not outcome:
            return Response({
                "status": False,
                "message": "Learning outcome not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = LearningOutcomeUpdateSerializer(outcome, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = LearningOutcomeDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Learning outcome updated.",
                "data": {"learning_outcome": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Academic - Learning Outcomes"],
        responses={200: LearningOutcomeDeleteResponseSerializer, 403: LearningOutcomeDeleteResponseSerializer, 404: LearningOutcomeDeleteResponseSerializer},
        description="Delete a learning outcome (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, outcome_id):
        outcome = self.get_object(outcome_id)
        if not outcome:
            return Response({
                "status": False,
                "message": "Learning outcome not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = LearningOutcomeService.delete_outcome(outcome)
        if success:
            return Response({
                "status": True,
                "message": "Learning outcome deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete learning outcome.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LearningOutcomeReorderView(APIView):
    permission_classes = [IsAuthenticated]

    class ReorderSerializer(serializers.Serializer):
        outcome_ids = serializers.ListField(child=serializers.IntegerField())

    @extend_schema(
        tags=["Academic - Learning Outcomes"],
        request=ReorderSerializer,
        responses={200: LearningOutcomeReorderResponseSerializer, 400: LearningOutcomeReorderResponseSerializer},
        description="Reorder learning outcomes for a subject by providing list of outcome IDs in desired order."
    )
    @transaction.atomic
    def post(self, request, subject_id):
        serializer = self.ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        outcome_ids = serializer.validated_data['outcome_ids']
        success = LearningOutcomeService.reorder_outcomes(subject_id, outcome_ids)
        if success:
            return Response({
                "status": True,
                "message": "Learning outcomes reordered.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Reorder failed.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)