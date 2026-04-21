import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from assessments.models import Choice, Question
from assessments.serializers.choice import (
    ChoiceMinimalSerializer,
    ChoiceCreateSerializer,
    ChoiceUpdateSerializer,
    ChoiceDisplaySerializer,
)
from assessments.services.choice import ChoiceService
from assessments.services.question import QuestionService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# Helper to check if user can modify choices of a question
def can_modify_question(user, question):
    if user.is_staff:
        return True
    if question.assessment.teacher and question.assessment.teacher.user == user:
        return True
    return False

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ChoiceCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    question = serializers.IntegerField()
    choice_text = serializers.CharField()

class ChoiceCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ChoiceCreateResponseData(allow_null=True)

class ChoiceUpdateResponseData(serializers.Serializer):
    choice = ChoiceDisplaySerializer()

class ChoiceUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ChoiceUpdateResponseData(allow_null=True)

class ChoiceDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ChoiceDetailResponseData(serializers.Serializer):
    choice = ChoiceDisplaySerializer()

class ChoiceDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ChoiceDetailResponseData(allow_null=True)

class ChoiceListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ChoiceMinimalSerializer(many=True)

class ChoiceListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ChoiceListResponseData()

class BulkChoiceCreateItem(serializers.Serializer):
    text = serializers.CharField()
    is_correct = serializers.BooleanField(default=False)
    order = serializers.IntegerField(required=False)

class BulkChoiceCreateSerializer(serializers.Serializer):
    choices = serializers.ListField(child=BulkChoiceCreateItem())

class BulkChoiceCreateResponseData(serializers.Serializer):
    created = serializers.ListField(child=serializers.IntegerField())
    count = serializers.IntegerField()

class BulkChoiceCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BulkChoiceCreateResponseData()

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

class ChoiceListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Assessments - Choices"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="question_id", type=int, description="Filter by question ID", required=False),
        ],
        responses={200: ChoiceListResponseSerializer},
        description="List choices, optionally filtered by question."
    )
    def get(self, request):
        question_id = request.query_params.get("question_id")
        if question_id:
            choices = ChoiceService.get_choices_by_question(question_id)
        else:
            choices = Choice.objects.all().select_related('question').order_by('order')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(choices, request)
        data = wrap_paginated_data(paginator, page, request, ChoiceMinimalSerializer)
        return Response({
            "status": True,
            "message": "Choices retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments - Choices"],
        request=ChoiceCreateSerializer,
        responses={201: ChoiceCreateResponseSerializer, 400: ChoiceCreateResponseSerializer},
        description="Create a new choice for a question (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = ChoiceCreateSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data.get('question')
            if not can_modify_question(request.user, question):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            choice = serializer.save()
            return Response({
                "status": True,
                "message": "Choice created.",
                "data": {
                    "id": choice.id,
                    "question": choice.question.id,
                    "choice_text": choice.choice_text,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChoiceDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, choice_id):
        return ChoiceService.get_choice_by_id(choice_id)

    @extend_schema(
        tags=["Assessments - Choices"],
        responses={200: ChoiceDetailResponseSerializer, 404: ChoiceDetailResponseSerializer},
        description="Retrieve a single choice by ID."
    )
    def get(self, request, choice_id):
        choice = self.get_object(choice_id)
        if not choice:
            return Response({
                "status": False,
                "message": "Choice not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = ChoiceDisplaySerializer(choice, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Choice retrieved.",
            "data": {"choice": data}
        })

    @extend_schema(
        tags=["Assessments - Choices"],
        request=ChoiceUpdateSerializer,
        responses={200: ChoiceUpdateResponseSerializer, 400: ChoiceUpdateResponseSerializer, 403: ChoiceUpdateResponseSerializer},
        description="Update a choice (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, choice_id):
        return self._update(request, choice_id, partial=False)

    @extend_schema(
        tags=["Assessments - Choices"],
        request=ChoiceUpdateSerializer,
        responses={200: ChoiceUpdateResponseSerializer, 400: ChoiceUpdateResponseSerializer, 403: ChoiceUpdateResponseSerializer},
        description="Partially update a choice."
    )
    @transaction.atomic
    def patch(self, request, choice_id):
        return self._update(request, choice_id, partial=True)

    def _update(self, request, choice_id, partial):
        choice = self.get_object(choice_id)
        if not choice:
            return Response({
                "status": False,
                "message": "Choice not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if not can_modify_question(user, choice.question):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ChoiceUpdateSerializer(choice, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ChoiceDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Choice updated.",
                "data": {"choice": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Assessments - Choices"],
        responses={200: ChoiceDeleteResponseSerializer, 403: ChoiceDeleteResponseSerializer, 404: ChoiceDeleteResponseSerializer},
        description="Delete a choice (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, choice_id):
        choice = self.get_object(choice_id)
        if not choice:
            return Response({
                "status": False,
                "message": "Choice not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not can_modify_question(user, choice.question):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = ChoiceService.delete_choice(choice)
        if success:
            return Response({
                "status": True,
                "message": "Choice deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete choice.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkChoiceCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Assessments - Choices"],
        request=BulkChoiceCreateSerializer,
        responses={201: BulkChoiceCreateResponseSerializer, 400: BulkChoiceCreateResponseSerializer},
        description="Bulk create choices for a question (teacher or admin only). Provide question_id as query param."
    )
    @transaction.atomic
    def post(self, request, question_id):
        question = QuestionService.get_question_by_id(question_id)
        if not question:
            return Response({
                "status": False,
                "message": "Question not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_modify_question(request.user, question):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = BulkChoiceCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        choices_data = serializer.validated_data['choices']
        # Build list of dicts with question
        full_data = []
        for idx, data in enumerate(choices_data):
            full_data.append({
                'question': question,
                'choice_text': data['text'],
                'is_correct': data.get('is_correct', False),
                'order': data.get('order', idx)
            })
        choices = ChoiceService.bulk_create_choices(question, full_data)
        created_ids = [c.id for c in choices]
        return Response({
            "status": True,
            "message": f"{len(created_ids)} choices created.",
            "data": {"created": created_ids, "count": len(created_ids)}
        }, status=status.HTTP_201_CREATED)