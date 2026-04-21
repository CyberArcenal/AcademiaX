import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from assessments.models import Question
from assessments.serializers.question import (
    QuestionMinimalSerializer,
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
    QuestionDisplaySerializer,
)
from assessments.services.assessment import AssessmentService
from assessments.services.question import QuestionService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class QuestionCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    assessment = serializers.IntegerField()
    question_text = serializers.CharField()

class QuestionCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = QuestionCreateResponseData(allow_null=True)

class QuestionUpdateResponseData(serializers.Serializer):
    question = QuestionDisplaySerializer()

class QuestionUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = QuestionUpdateResponseData(allow_null=True)

class QuestionDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class QuestionDetailResponseData(serializers.Serializer):
    question = QuestionDisplaySerializer()

class QuestionDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = QuestionDetailResponseData(allow_null=True)

class QuestionListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = QuestionMinimalSerializer(many=True)

class QuestionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = QuestionListResponseData()

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

# Helper to check if user can modify questions of an assessment
def can_modify_assessment(user, assessment):
    if user.is_staff:
        return True
    if assessment.teacher and assessment.teacher.user == user:
        return True
    return False

# ----------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------

class QuestionListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Assessments - Questions"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="assessment_id", type=int, description="Filter by assessment ID", required=False),
        ],
        responses={200: QuestionListResponseSerializer},
        description="List questions, optionally filtered by assessment."
    )
    def get(self, request):
        assessment_id = request.query_params.get("assessment_id")
        if assessment_id:
            questions = QuestionService.get_questions_by_assessment(assessment_id)
        else:
            questions = Question.objects.all().select_related('assessment').order_by('order')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(questions, request)
        data = wrap_paginated_data(paginator, page, request, QuestionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Questions retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments - Questions"],
        request=QuestionCreateSerializer,
        responses={201: QuestionCreateResponseSerializer, 400: QuestionCreateResponseSerializer},
        description="Create a new question (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Validate assessment ownership via serializer context? We'll check after partial validation.
        serializer = QuestionCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Check permission on the assessment
            assessment = serializer.validated_data.get('assessment')
            if not can_modify_assessment(request.user, assessment):
                return Response({
                    "status": False,
                    "message": "You do not have permission to add questions to this assessment.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            question = serializer.save()
            return Response({
                "status": True,
                "message": "Question created.",
                "data": {
                    "id": question.id,
                    "assessment": question.assessment.id,
                    "question_text": question.question_text,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class QuestionDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, question_id):
        return QuestionService.get_question_by_id(question_id)

    @extend_schema(
        tags=["Assessments - Questions"],
        responses={200: QuestionDetailResponseSerializer, 404: QuestionDetailResponseSerializer},
        description="Retrieve a single question by ID."
    )
    def get(self, request, question_id):
        question = self.get_object(question_id)
        if not question:
            return Response({
                "status": False,
                "message": "Question not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = QuestionDisplaySerializer(question, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Question retrieved.",
            "data": {"question": data}
        })

    @extend_schema(
        tags=["Assessments - Questions"],
        request=QuestionUpdateSerializer,
        responses={200: QuestionUpdateResponseSerializer, 400: QuestionUpdateResponseSerializer, 403: QuestionUpdateResponseSerializer},
        description="Update a question (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, question_id):
        return self._update(request, question_id, partial=False)

    @extend_schema(
        tags=["Assessments - Questions"],
        request=QuestionUpdateSerializer,
        responses={200: QuestionUpdateResponseSerializer, 400: QuestionUpdateResponseSerializer, 403: QuestionUpdateResponseSerializer},
        description="Partially update a question."
    )
    @transaction.atomic
    def patch(self, request, question_id):
        return self._update(request, question_id, partial=True)

    def _update(self, request, question_id, partial):
        question = self.get_object(question_id)
        if not question:
            return Response({
                "status": False,
                "message": "Question not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if not can_modify_assessment(user, question.assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = QuestionUpdateSerializer(question, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = QuestionDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Question updated.",
                "data": {"question": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Assessments - Questions"],
        responses={200: QuestionDeleteResponseSerializer, 403: QuestionDeleteResponseSerializer, 404: QuestionDeleteResponseSerializer},
        description="Delete a question (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, question_id):
        question = self.get_object(question_id)
        if not question:
            return Response({
                "status": False,
                "message": "Question not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not can_modify_assessment(user, question.assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = QuestionService.delete_question(question)
        if success:
            return Response({
                "status": True,
                "message": "Question deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete question.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuestionReorderView(APIView):
    permission_classes = [IsAuthenticated]

    class ReorderSerializer(serializers.Serializer):
        question_ids = serializers.ListField(child=serializers.IntegerField())

    @extend_schema(
        tags=["Assessments - Questions"],
        request=ReorderSerializer,
        responses={200: serializers.Serializer, 400: serializers.Serializer, 403: serializers.Serializer},
        description="Reorder questions within an assessment (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request, assessment_id):
        from assessments.models import Assessment
        assessment = AssessmentService.get_assessment_by_id(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_modify_assessment(request.user, assessment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        question_ids = serializer.validated_data['question_ids']
        success = QuestionService.reorder_questions(assessment_id, question_ids)
        if success:
            return Response({
                "status": True,
                "message": "Questions reordered.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Reorder failed.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)