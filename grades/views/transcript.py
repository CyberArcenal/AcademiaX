import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from grades.models import Transcript
from grades.serializers.transcript import (
    TranscriptMinimalSerializer,
    TranscriptCreateSerializer,
    TranscriptUpdateSerializer,
    TranscriptDisplaySerializer,
)
from grades.services.transcript import TranscriptService

logger = logging.getLogger(__name__)

def can_view_transcript(user, transcript):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return transcript.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return transcript.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        # Teacher can view transcript for students they teach
        teacher = user.teacher_profile
        sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
        from enrollments.models import Enrollment
        student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
        return transcript.student_id in student_ids
    return False

def can_manage_transcript(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TranscriptCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    cumulative_gwa = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

class TranscriptCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TranscriptCreateResponseData(allow_null=True)

class TranscriptUpdateResponseData(serializers.Serializer):
    transcript = TranscriptDisplaySerializer()

class TranscriptUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TranscriptUpdateResponseData(allow_null=True)

class TranscriptDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TranscriptDetailResponseData(serializers.Serializer):
    transcript = TranscriptDisplaySerializer()

class TranscriptDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TranscriptDetailResponseData(allow_null=True)

class TranscriptListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TranscriptMinimalSerializer(many=True)

class TranscriptListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TranscriptListResponseData()

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

class TranscriptListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Transcripts"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
        ],
        responses={200: TranscriptListResponseSerializer},
        description="List transcripts (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")

        if user.is_staff or can_manage_transcript(user):
            queryset = Transcript.objects.all().select_related('student')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = Transcript.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = Transcript.objects.filter(student_id__in=child_ids)
            elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                teacher = user.teacher_profile
                sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                from enrollments.models import Enrollment
                student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
                queryset = Transcript.objects.filter(student_id__in=student_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, TranscriptMinimalSerializer)
        return Response({
            "status": True,
            "message": "Transcripts retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Grades - Transcripts"],
        request=TranscriptCreateSerializer,
        responses={201: TranscriptCreateResponseSerializer, 400: TranscriptCreateResponseSerializer, 403: TranscriptCreateResponseSerializer},
        description="Create a transcript (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_transcript(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = TranscriptCreateSerializer(data=request.data)
        if serializer.is_valid():
            transcript = serializer.save()
            return Response({
                "status": True,
                "message": "Transcript created.",
                "data": {
                    "id": transcript.id,
                    "student": transcript.student.id,
                    "cumulative_gwa": transcript.cumulative_gwa,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TranscriptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, transcript_id):
        try:
            return Transcript.objects.select_related('student').get(id=transcript_id)
        except Transcript.DoesNotExist:
            return None

    @extend_schema(
        tags=["Grades - Transcripts"],
        responses={200: TranscriptDetailResponseSerializer, 404: TranscriptDetailResponseSerializer, 403: TranscriptDetailResponseSerializer},
        description="Retrieve a single transcript by ID."
    )
    def get(self, request, transcript_id):
        transcript = self.get_object(transcript_id)
        if not transcript:
            return Response({
                "status": False,
                "message": "Transcript not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_transcript(request.user, transcript):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = TranscriptDisplaySerializer(transcript, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Transcript retrieved.",
            "data": {"transcript": data}
        })

    @extend_schema(
        tags=["Grades - Transcripts"],
        request=TranscriptUpdateSerializer,
        responses={200: TranscriptUpdateResponseSerializer, 400: TranscriptUpdateResponseSerializer, 403: TranscriptUpdateResponseSerializer},
        description="Update a transcript (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, transcript_id):
        return self._update(request, transcript_id, partial=False)

    @extend_schema(
        tags=["Grades - Transcripts"],
        request=TranscriptUpdateSerializer,
        responses={200: TranscriptUpdateResponseSerializer, 400: TranscriptUpdateResponseSerializer, 403: TranscriptUpdateResponseSerializer},
        description="Partially update a transcript."
    )
    @transaction.atomic
    def patch(self, request, transcript_id):
        return self._update(request, transcript_id, partial=True)

    def _update(self, request, transcript_id, partial):
        if not can_manage_transcript(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        transcript = self.get_object(transcript_id)
        if not transcript:
            return Response({
                "status": False,
                "message": "Transcript not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TranscriptUpdateSerializer(transcript, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = TranscriptDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Transcript updated.",
                "data": {"transcript": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Grades - Transcripts"],
        responses={200: TranscriptDeleteResponseSerializer, 403: TranscriptDeleteResponseSerializer, 404: TranscriptDeleteResponseSerializer},
        description="Delete a transcript (admin only)."
    )
    @transaction.atomic
    def delete(self, request, transcript_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        transcript = self.get_object(transcript_id)
        if not transcript:
            return Response({
                "status": False,
                "message": "Transcript not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = TranscriptService.delete_transcript(transcript)
        if success:
            return Response({
                "status": True,
                "message": "Transcript deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete transcript.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TranscriptComputeGWAView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Transcripts"],
        responses={200: TranscriptUpdateResponseSerializer, 403: TranscriptUpdateResponseSerializer, 404: TranscriptUpdateResponseSerializer},
        description="Compute cumulative GWA from final grades and update transcript (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request, transcript_id):
        if not can_manage_transcript(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        transcript = TranscriptService.get_transcript_by_id(transcript_id)
        if not transcript:
            return Response({
                "status": False,
                "message": "Transcript not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        gwa = TranscriptService.compute_cumulative_gwa(transcript.student.id)
        updated = TranscriptService.update_transcript(transcript, {'cumulative_gwa': gwa})
        data = TranscriptDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Cumulative GWA computed and transcript updated.",
            "data": {"transcript": data}
        })


class TranscriptMarkOfficialView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Transcripts"],
        responses={200: TranscriptUpdateResponseSerializer, 403: TranscriptUpdateResponseSerializer, 404: TranscriptUpdateResponseSerializer},
        description="Mark transcript as official (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request, transcript_id):
        if not can_manage_transcript(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        transcript = TranscriptService.get_transcript_by_id(transcript_id)
        if not transcript:
            return Response({
                "status": False,
                "message": "Transcript not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = TranscriptService.mark_official(transcript)
        data = TranscriptDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Transcript marked as official.",
            "data": {"transcript": data}
        })