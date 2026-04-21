import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from assessments.models import Answer, Submission, Question
from assessments.serializers.answer import (
    AnswerMinimalSerializer,
    AnswerCreateSerializer,
    AnswerUpdateSerializer,
    AnswerDisplaySerializer,
)
from assessments.services.answer import AnswerService
from assessments.services.submission import SubmissionService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# Helper to check if user can grade answers (teacher of assessment or admin)
def can_grade_submission(user, submission):
    if user.is_staff:
        return True
    if submission.assessment.teacher and submission.assessment.teacher.user == user:
        return True
    return False

def can_view_submission(user, submission):
    if user.is_staff or can_grade_submission(user, submission):
        return True
    if submission.student.user == user:
        return True
    return False

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AnswerCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    submission = serializers.IntegerField()
    question = serializers.IntegerField()

class AnswerCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnswerCreateResponseData(allow_null=True)

class AnswerUpdateResponseData(serializers.Serializer):
    answer = AnswerDisplaySerializer()

class AnswerUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnswerUpdateResponseData(allow_null=True)

class AnswerDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AnswerDetailResponseData(serializers.Serializer):
    answer = AnswerDisplaySerializer()

class AnswerDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnswerDetailResponseData(allow_null=True)

class AnswerListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AnswerMinimalSerializer(many=True)

class AnswerListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AnswerListResponseData()

class AnswerGradeRequestSerializer(serializers.Serializer):
    points_earned = serializers.DecimalField(max_digits=6, decimal_places=2)
    feedback = serializers.CharField(required=False, allow_blank=True)

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

class AnswerListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Assessments - Answers"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="submission_id", type=int, description="Filter by submission ID", required=False),
        ],
        responses={200: AnswerListResponseSerializer},
        description="List answers for a submission (student sees own, teacher sees all for assessment)."
    )
    def get(self, request):
        submission_id = request.query_params.get("submission_id")
        if not submission_id:
            return Response({
                "status": False,
                "message": "submission_id parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        submission = SubmissionService.get_submission_by_id(submission_id)
        if not submission:
            return Response({
                "status": False,
                "message": "Submission not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        if not can_view_submission(request.user, submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        answers = AnswerService.get_answers_by_submission(submission_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(answers, request)
        data = wrap_paginated_data(paginator, page, request, AnswerMinimalSerializer)
        return Response({
            "status": True,
            "message": "Answers retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments - Answers"],
        request=AnswerCreateSerializer,
        responses={201: AnswerCreateResponseSerializer, 400: AnswerCreateResponseSerializer, 403: AnswerCreateResponseSerializer},
        description="Create an answer for a submission (student only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Only students can answer
        if request.user.role != 'STUDENT':
            return Response({
                "status": False,
                "message": "Only students can submit answers.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AnswerCreateSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.validated_data.get('submission')
            # Ensure the student owns the submission
            if not submission.student.user == request.user:
                return Response({
                    "status": False,
                    "message": "You can only answer your own submissions.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            answer = serializer.save()
            return Response({
                "status": True,
                "message": "Answer created.",
                "data": {
                    "id": answer.id,
                    "submission": answer.submission.id,
                    "question": answer.question.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AnswerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, answer_id):
        return AnswerService.get_answer_by_id(answer_id)

    @extend_schema(
        tags=["Assessments - Answers"],
        responses={200: AnswerDetailResponseSerializer, 404: AnswerDetailResponseSerializer, 403: AnswerDetailResponseSerializer},
        description="Retrieve a single answer by ID (owner or teacher)."
    )
    def get(self, request, answer_id):
        answer = self.get_object(answer_id)
        if not answer:
            return Response({
                "status": False,
                "message": "Answer not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_submission(request.user, answer.submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = AnswerDisplaySerializer(answer, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Answer retrieved.",
            "data": {"answer": data}
        })

    @extend_schema(
        tags=["Assessments - Answers"],
        request=AnswerUpdateSerializer,
        responses={200: AnswerUpdateResponseSerializer, 400: AnswerUpdateResponseSerializer, 403: AnswerUpdateResponseSerializer},
        description="Update an answer (student can update before graded; teacher can grade)."
    )
    @transaction.atomic
    def put(self, request, answer_id):
        return self._update(request, answer_id, partial=False)

    @extend_schema(
        tags=["Assessments - Answers"],
        request=AnswerUpdateSerializer,
        responses={200: AnswerUpdateResponseSerializer, 400: AnswerUpdateResponseSerializer, 403: AnswerUpdateResponseSerializer},
        description="Partially update an answer."
    )
    @transaction.atomic
    def patch(self, request, answer_id):
        return self._update(request, answer_id, partial=True)

    def _update(self, request, answer_id, partial):
        answer = self.get_object(answer_id)
        if not answer:
            return Response({
                "status": False,
                "message": "Answer not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        # If student owns the submission and answer not yet graded, allow update
        submission = answer.submission
        if user.role == 'STUDENT' and submission.student.user == user:
            # Student can update only if not graded yet
            if submission.status != 'GD':
                serializer = AnswerUpdateSerializer(answer, data=request.data, partial=partial)
                if serializer.is_valid():
                    updated = serializer.save()
                    data = AnswerDisplaySerializer(updated, context={"request": request}).data
                    return Response({
                        "status": True,
                        "message": "Answer updated.",
                        "data": {"answer": data}
                    })
                return Response({
                    "status": False,
                    "message": "Validation error.",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "status": False,
                    "message": "Cannot update answer after grading.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
        # Teacher can grade (update points_earned, feedback)
        elif can_grade_submission(user, submission):
            serializer = AnswerUpdateSerializer(answer, data=request.data, partial=partial)
            if serializer.is_valid():
                updated = serializer.save()
                data = AnswerDisplaySerializer(updated, context={"request": request}).data
                return Response({
                    "status": True,
                    "message": "Answer updated.",
                    "data": {"answer": data}
                })
            return Response({
                "status": False,
                "message": "Validation error.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

    @extend_schema(
        tags=["Assessments - Answers"],
        responses={200: AnswerDeleteResponseSerializer, 403: AnswerDeleteResponseSerializer, 404: AnswerDeleteResponseSerializer},
        description="Delete an answer (teacher or admin only)."
    )
    @transaction.atomic
    def delete(self, request, answer_id):
        answer = self.get_object(answer_id)
        if not answer:
            return Response({
                "status": False,
                "message": "Answer not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_grade_submission(request.user, answer.submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = AnswerService.delete_answer(answer)
        if success:
            return Response({
                "status": True,
                "message": "Answer deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete answer.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnswerGradeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Assessments - Answers"],
        request=AnswerGradeRequestSerializer,
        responses={200: AnswerUpdateResponseSerializer, 400: AnswerUpdateResponseSerializer, 403: AnswerUpdateResponseSerializer},
        description="Grade a single answer (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request, answer_id):
        answer = AnswerService.get_answer_by_id(answer_id)
        if not answer:
            return Response({
                "status": False,
                "message": "Answer not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_grade_submission(request.user, answer.submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AnswerGradeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        points_earned = serializer.validated_data['points_earned']
        feedback = serializer.validated_data.get('feedback', '')
        graded = AnswerService.grade_answer(answer, points_earned, feedback)
        data = AnswerDisplaySerializer(graded, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Answer graded.",
            "data": {"answer": data}
        })