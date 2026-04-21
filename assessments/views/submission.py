import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from assessments.models import Submission
from assessments.serializers.submission import (
    SubmissionMinimalSerializer,
    SubmissionCreateSerializer,
    SubmissionUpdateSerializer,
    SubmissionDisplaySerializer,
)
from assessments.services.submission import SubmissionService
from assessments.services.assessment import AssessmentService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class SubmissionCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    assessment = serializers.IntegerField()
    student = serializers.IntegerField()
    status = serializers.CharField()

class SubmissionCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubmissionCreateResponseData(allow_null=True)

class SubmissionUpdateResponseData(serializers.Serializer):
    submission = SubmissionDisplaySerializer()

class SubmissionUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubmissionUpdateResponseData(allow_null=True)

class SubmissionDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class SubmissionDetailResponseData(serializers.Serializer):
    submission = SubmissionDisplaySerializer()

class SubmissionDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubmissionDetailResponseData(allow_null=True)

class SubmissionListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SubmissionMinimalSerializer(many=True)

class SubmissionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubmissionListResponseData()

class SubmissionGradeRequestSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=6, decimal_places=2)
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

# Helper to check if user can grade a submission (teacher of assessment or admin)
def can_grade_submission(user, submission):
    if user.is_staff:
        return True
    if submission.assessment.teacher and submission.assessment.teacher.user == user:
        return True
    return False

def can_view_submission(user, submission):
    # Student can view own submission; teacher/admin can view any
    if user.is_staff or can_grade_submission(user, submission):
        return True
    if submission.student.user == user:
        return True
    return False

# ----------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------

class SubmissionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Assessments - Submissions"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="assessment_id", type=int, description="Filter by assessment ID", required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
        ],
        responses={200: SubmissionListResponseSerializer},
        description="List submissions. Students see only their own; teachers see submissions for their assessments."
    )
    def get(self, request):
        user = request.user
        assessment_id = request.query_params.get("assessment_id")
        student_id = request.query_params.get("student_id")

        if user.role == 'STUDENT':
            # Students can only see their own submissions
            submissions = SubmissionService.get_submissions_by_student(user.student_profile.id)
        else:
            # Teachers and admins can filter
            if assessment_id:
                submissions = SubmissionService.get_submissions_by_assessment(assessment_id)
            elif student_id:
                submissions = SubmissionService.get_submissions_by_student(student_id)
            else:
                submissions = Submission.objects.all().select_related('assessment', 'student')
        submissions = submissions.order_by('-submitted_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(submissions, request)
        data = wrap_paginated_data(paginator, page, request, SubmissionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Submissions retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments - Submissions"],
        request=SubmissionCreateSerializer,
        responses={201: SubmissionCreateResponseSerializer, 400: SubmissionCreateResponseSerializer, 403: SubmissionCreateResponseSerializer},
        description="Submit an assessment (student only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Only students can submit
        if request.user.role != 'STUDENT':
            return Response({
                "status": False,
                "message": "Only students can submit assessments.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = SubmissionCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            submission = serializer.save()
            return Response({
                "status": True,
                "message": "Submission created.",
                "data": {
                    "id": submission.id,
                    "assessment": submission.assessment.id,
                    "student": submission.student.id,
                    "status": submission.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, submission_id):
        return SubmissionService.get_submission_by_id(submission_id)

    @extend_schema(
        tags=["Assessments - Submissions"],
        responses={200: SubmissionDetailResponseSerializer, 404: SubmissionDetailResponseSerializer, 403: SubmissionDetailResponseSerializer},
        description="Retrieve a single submission by ID (owner or teacher)."
    )
    def get(self, request, submission_id):
        submission = self.get_object(submission_id)
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
        data = SubmissionDisplaySerializer(submission, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Submission retrieved.",
            "data": {"submission": data}
        })

    @extend_schema(
        tags=["Assessments - Submissions"],
        request=SubmissionUpdateSerializer,
        responses={200: SubmissionUpdateResponseSerializer, 400: SubmissionUpdateResponseSerializer, 403: SubmissionUpdateResponseSerializer},
        description="Update a submission (e.g., change status). Usually only teacher can grade."
    )
    @transaction.atomic
    def put(self, request, submission_id):
        return self._update(request, submission_id, partial=False)

    @extend_schema(
        tags=["Assessments - Submissions"],
        request=SubmissionUpdateSerializer,
        responses={200: SubmissionUpdateResponseSerializer, 400: SubmissionUpdateResponseSerializer, 403: SubmissionUpdateResponseSerializer},
        description="Partially update a submission."
    )
    @transaction.atomic
    def patch(self, request, submission_id):
        return self._update(request, submission_id, partial=True)

    def _update(self, request, submission_id, partial):
        submission = self.get_object(submission_id)
        if not submission:
            return Response({
                "status": False,
                "message": "Submission not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Only teacher or admin can update submission (grading)
        if not can_grade_submission(request.user, submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmissionUpdateSerializer(submission, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = SubmissionDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Submission updated.",
                "data": {"submission": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Assessments - Submissions"],
        responses={200: SubmissionDeleteResponseSerializer, 403: SubmissionDeleteResponseSerializer, 404: SubmissionDeleteResponseSerializer},
        description="Delete a submission (teacher or admin only)."
    )
    @transaction.atomic
    def delete(self, request, submission_id):
        submission = self.get_object(submission_id)
        if not submission:
            return Response({
                "status": False,
                "message": "Submission not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_grade_submission(request.user, submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = SubmissionService.delete_submission(submission)
        if success:
            return Response({
                "status": True,
                "message": "Submission deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete submission.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubmissionGradeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Assessments - Submissions"],
        request=SubmissionGradeRequestSerializer,
        responses={200: SubmissionUpdateResponseSerializer, 400: SubmissionUpdateResponseSerializer, 403: SubmissionUpdateResponseSerializer},
        description="Grade a submission (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request, submission_id):
        submission = SubmissionService.get_submission_by_id(submission_id)
        if not submission:
            return Response({
                "status": False,
                "message": "Submission not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_grade_submission(request.user, submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmissionGradeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        score = serializer.validated_data['score']
        feedback = serializer.validated_data.get('feedback', '')
        graded = SubmissionService.grade_submission(submission, score, request.user.id, feedback)
        data = SubmissionDisplaySerializer(graded, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Submission graded.",
            "data": {"submission": data}
        })