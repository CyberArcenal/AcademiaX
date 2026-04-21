import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from assessments.models import Assessment
from assessments.serializers.assessment import (
    AssessmentMinimalSerializer,
    AssessmentCreateSerializer,
    AssessmentUpdateSerializer,
    AssessmentDisplaySerializer,
)
from assessments.services.assessment import AssessmentService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AssessmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    subject = serializers.IntegerField()

class AssessmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AssessmentCreateResponseData(allow_null=True)

class AssessmentUpdateResponseData(serializers.Serializer):
    assessment = AssessmentDisplaySerializer()

class AssessmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AssessmentUpdateResponseData(allow_null=True)

class AssessmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AssessmentDetailResponseData(serializers.Serializer):
    assessment = AssessmentDisplaySerializer()

class AssessmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AssessmentDetailResponseData(allow_null=True)

class AssessmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AssessmentMinimalSerializer(many=True)

class AssessmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AssessmentListResponseData()

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

class AssessmentListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Assessments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject ID", required=False),
            OpenApiParameter(name="teacher_id", type=int, description="Filter by teacher ID", required=False),
            OpenApiParameter(name="published_only", type=bool, description="Only published assessments", required=False),
        ],
        responses={200: AssessmentListResponseSerializer},
        description="List assessments, optionally filtered by subject, teacher, or published status."
    )
    def get(self, request):
        subject_id = request.query_params.get("subject_id")
        teacher_id = request.query_params.get("teacher_id")
        published_only = request.query_params.get("published_only", "true").lower() == "true"
        if subject_id:
            assessments = AssessmentService.get_assessments_by_subject(subject_id, published_only=published_only)
        elif teacher_id:
            assessments = Assessment.objects.filter(teacher_id=teacher_id)
            if published_only:
                assessments = assessments.filter(is_published=True)
        else:
            assessments = Assessment.objects.all()
            if published_only:
                assessments = assessments.filter(is_published=True)
        assessments = assessments.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(assessments, request)
        data = wrap_paginated_data(paginator, page, request, AssessmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Assessments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Assessments"],
        request=AssessmentCreateSerializer,
        responses={201: AssessmentCreateResponseSerializer, 400: AssessmentCreateResponseSerializer},
        description="Create a new assessment (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Only teachers or staff can create assessments
        if not (request.user.role == 'TEACHER' or request.user.is_staff):
            return Response({
                "status": False,
                "message": "Teacher permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = AssessmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            assessment = serializer.save()
            return Response({
                "status": True,
                "message": "Assessment created.",
                "data": {
                    "id": assessment.id,
                    "title": assessment.title,
                    "subject": assessment.subject.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AssessmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, assessment_id):
        return AssessmentService.get_assessment_by_id(assessment_id)

    @extend_schema(
        tags=["Assessments"],
        responses={200: AssessmentDetailResponseSerializer, 404: AssessmentDetailResponseSerializer},
        description="Retrieve a single assessment by ID."
    )
    def get(self, request, assessment_id):
        assessment = self.get_object(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = AssessmentDisplaySerializer(assessment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Assessment retrieved.",
            "data": {"assessment": data}
        })

    @extend_schema(
        tags=["Assessments"],
        request=AssessmentUpdateSerializer,
        responses={200: AssessmentUpdateResponseSerializer, 400: AssessmentUpdateResponseSerializer, 403: AssessmentUpdateResponseSerializer},
        description="Update an assessment (teacher or admin only)."
    )
    @transaction.atomic
    def put(self, request, assessment_id):
        return self._update(request, assessment_id, partial=False)

    @extend_schema(
        tags=["Assessments"],
        request=AssessmentUpdateSerializer,
        responses={200: AssessmentUpdateResponseSerializer, 400: AssessmentUpdateResponseSerializer, 403: AssessmentUpdateResponseSerializer},
        description="Partially update an assessment."
    )
    @transaction.atomic
    def patch(self, request, assessment_id):
        return self._update(request, assessment_id, partial=True)

    def _update(self, request, assessment_id, partial):
        assessment = self.get_object(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Allow teacher who created the assessment or staff
        if not (user.is_staff or (assessment.teacher.user and user == assessment.teacher.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AssessmentUpdateSerializer(assessment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AssessmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Assessment updated.",
                "data": {"assessment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Assessments"],
        parameters=[OpenApiParameter(name="hard", type=bool, required=False)],
        responses={200: AssessmentDeleteResponseSerializer, 403: AssessmentDeleteResponseSerializer, 404: AssessmentDeleteResponseSerializer},
        description="Delete an assessment (soft delete by default)."
    )
    @transaction.atomic
    def delete(self, request, assessment_id):
        assessment = self.get_object(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not (user.is_staff or (assessment.teacher.user and user == assessment.teacher.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        hard = request.query_params.get("hard", "false").lower() == "true"
        success = AssessmentService.delete_assessment(assessment, soft_delete=not hard)
        if success:
            return Response({
                "status": True,
                "message": "Assessment deleted successfully." + (" (permanent)" if hard else ""),
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete assessment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssessmentPublishView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Assessments"],
        responses={200: AssessmentUpdateResponseSerializer, 403: AssessmentUpdateResponseSerializer, 404: AssessmentUpdateResponseSerializer},
        description="Publish an assessment (teacher or admin only)."
    )
    @transaction.atomic
    def post(self, request, assessment_id):
        assessment = AssessmentService.get_assessment_by_id(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not (user.is_staff or (assessment.teacher.user and user == assessment.teacher.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        updated = AssessmentService.publish_assessment(assessment)
        data = AssessmentDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Assessment published.",
            "data": {"assessment": data}
        })

    @extend_schema(
        tags=["Assessments"],
        responses={200: AssessmentUpdateResponseSerializer, 403: AssessmentUpdateResponseSerializer, 404: AssessmentUpdateResponseSerializer},
        description="Unpublish an assessment (teacher or admin only)."
    )
    @transaction.atomic
    def delete(self, request, assessment_id):
        assessment = AssessmentService.get_assessment_by_id(assessment_id)
        if not assessment:
            return Response({
                "status": False,
                "message": "Assessment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not (user.is_staff or (assessment.teacher.user and user == assessment.teacher.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        updated = AssessmentService.unpublish_assessment(assessment)
        data = AssessmentDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Assessment unpublished.",
            "data": {"assessment": data}
        })