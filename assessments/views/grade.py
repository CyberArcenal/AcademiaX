import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from assessments.models import AssessmentGrade
from assessments.serializers.grade import (
    AssessmentGradeMinimalSerializer,
    AssessmentGradeCreateSerializer,
    AssessmentGradeUpdateSerializer,
    AssessmentGradeDisplaySerializer,
)
from assessments.services.grade import AssessmentGradeService
from assessments.services.submission import SubmissionService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# Helper to check if user can grade submission (teacher or admin)
def can_grade_submission(user, submission):
    if user.is_staff:
        return True
    if submission.assessment.teacher and submission.assessment.teacher.user == user:
        return True
    return False

def can_view_grade(user, grade):
    if user.is_staff:
        return True
    submission = grade.submission
    if submission.assessment.teacher and submission.assessment.teacher.user == user:
        return True
    if submission.student.user == user:
        return True
    return False

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class GradeCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    submission = serializers.IntegerField()
    raw_score = serializers.DecimalField(max_digits=6, decimal_places=2)

class GradeCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeCreateResponseData(allow_null=True)

class GradeUpdateResponseData(serializers.Serializer):
    grade = AssessmentGradeDisplaySerializer()

class GradeUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeUpdateResponseData(allow_null=True)

class GradeDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class GradeDetailResponseData(serializers.Serializer):
    grade = AssessmentGradeDisplaySerializer()

class GradeDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeDetailResponseData(allow_null=True)

class GradeListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AssessmentGradeMinimalSerializer(many=True)

class GradeListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = GradeListResponseData()

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

class AssessmentGradeListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Assessments - Grades"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="submission_id", type=int, description="Filter by submission ID", required=False),
        ],
        responses={200: GradeListResponseSerializer},
        description="List assessment grades (student sees own, teacher sees all for assessment)."
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

        # Students can only see their own grades
        if request.user.role == 'STUDENT' and submission.student.user != request.user:
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        grade = AssessmentGradeService.get_grade_by_submission(submission_id)
        if grade:
            grades = [grade]
        else:
            grades = []
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(grades, request)
        data = wrap_paginated_data(paginator, page, request, AssessmentGradeMinimalSerializer)
        return Response({
            "status": True,
            "message": "Grades retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments - Grades"],
        request=AssessmentGradeCreateSerializer,
        responses={201: GradeCreateResponseSerializer, 400: GradeCreateResponseSerializer, 403: GradeCreateResponseSerializer},
        description="Create/update a grade for a submission (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AssessmentGradeCreateSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.validated_data.get('submission')
            if not can_grade_submission(request.user, submission):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            grade = serializer.save()
            return Response({
                "status": True,
                "message": "Grade saved.",
                "data": {
                    "id": grade.id,
                    "submission": grade.submission.id,
                    "raw_score": grade.raw_score,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AssessmentGradeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, grade_id):
        try:
            return AssessmentGrade.objects.select_related('submission__assessment', 'submission__student').get(id=grade_id)
        except AssessmentGrade.DoesNotExist:
            return None

    @extend_schema(
        tags=["Assessments - Grades"],
        responses={200: GradeDetailResponseSerializer, 404: GradeDetailResponseSerializer, 403: GradeDetailResponseSerializer},
        description="Retrieve a single assessment grade by ID."
    )
    def get(self, request, grade_id):
        grade = self.get_object(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_grade(request.user, grade):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = AssessmentGradeDisplaySerializer(grade, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Grade retrieved.",
            "data": {"grade": data}
        })

    @extend_schema(
        tags=["Assessments - Grades"],
        request=AssessmentGradeUpdateSerializer,
        responses={200: GradeUpdateResponseSerializer, 400: GradeUpdateResponseSerializer, 403: GradeUpdateResponseSerializer},
        description="Update an assessment grade (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, grade_id):
        return self._update(request, grade_id, partial=False)

    @extend_schema(
        tags=["Assessments - Grades"],
        request=AssessmentGradeUpdateSerializer,
        responses={200: GradeUpdateResponseSerializer, 400: GradeUpdateResponseSerializer, 403: GradeUpdateResponseSerializer},
        description="Partially update an assessment grade."
    )
    @transaction.atomic
    def patch(self, request, grade_id):
        return self._update(request, grade_id, partial=True)

    def _update(self, request, grade_id, partial):
        grade = self.get_object(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_grade_submission(request.user, grade.submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AssessmentGradeUpdateSerializer(grade, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AssessmentGradeDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Grade updated.",
                "data": {"grade": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Assessments - Grades"],
        responses={200: GradeDeleteResponseSerializer, 403: GradeDeleteResponseSerializer, 404: GradeDeleteResponseSerializer},
        description="Delete an assessment grade (teacher or admin only)."
    )
    @transaction.atomic
    def delete(self, request, grade_id):
        grade = self.get_object(grade_id)
        if not grade:
            return Response({
                "status": False,
                "message": "Grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_grade_submission(request.user, grade.submission):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = AssessmentGradeService.delete_grade(grade)
        if success:
            return Response({
                "status": True,
                "message": "Grade deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete grade.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)