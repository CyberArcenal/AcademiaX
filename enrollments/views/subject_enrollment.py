import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from enrollments.models import SubjectEnrollment
from enrollments.serializers.subject_enrollment import (
    SubjectEnrollmentMinimalSerializer,
    SubjectEnrollmentCreateSerializer,
    SubjectEnrollmentUpdateSerializer,
    SubjectEnrollmentDisplaySerializer,
)
from enrollments.services.subject_enrollment import SubjectEnrollmentService
from enrollments.services.enrollment import EnrollmentService

logger = logging.getLogger(__name__)

def can_view_subject_enrollment(user, subject_enrollment):
    if user.is_staff:
        return True
    if user.role == 'TEACHER':
        # Teacher can see if they are the teacher of the subject
        return subject_enrollment.teacher and subject_enrollment.teacher.user == user
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return subject_enrollment.enrollment.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return subject_enrollment.enrollment.student in [sp.student for sp in user.parent_profile.students.all()]
    return False

def can_manage_subject_enrollment(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class SubjectEnrollmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    enrollment = serializers.IntegerField()
    subject = serializers.IntegerField()

class SubjectEnrollmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectEnrollmentCreateResponseData(allow_null=True)

class SubjectEnrollmentUpdateResponseData(serializers.Serializer):
    subject_enrollment = SubjectEnrollmentDisplaySerializer()

class SubjectEnrollmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectEnrollmentUpdateResponseData(allow_null=True)

class SubjectEnrollmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class SubjectEnrollmentDetailResponseData(serializers.Serializer):
    subject_enrollment = SubjectEnrollmentDisplaySerializer()

class SubjectEnrollmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectEnrollmentDetailResponseData(allow_null=True)

class SubjectEnrollmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SubjectEnrollmentMinimalSerializer(many=True)

class SubjectEnrollmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectEnrollmentListResponseData()

class SubjectEnrollmentDropResponseData(serializers.Serializer):
    subject_enrollment = SubjectEnrollmentDisplaySerializer()

class SubjectEnrollmentDropResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SubjectEnrollmentDropResponseData()

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

class SubjectEnrollmentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Enrollments - Subject Enrollments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="enrollment_id", type=int, description="Filter by enrollment ID", required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID (via enrollment)", required=False),
        ],
        responses={200: SubjectEnrollmentListResponseSerializer},
        description="List subject enrollments (filtered by enrollment or student)."
    )
    def get(self, request):
        enrollment_id = request.query_params.get("enrollment_id")
        student_id = request.query_params.get("student_id")
        queryset = SubjectEnrollment.objects.all().select_related('enrollment', 'subject', 'teacher')
        if enrollment_id:
            queryset = queryset.filter(enrollment_id=enrollment_id)
        elif student_id:
            queryset = queryset.filter(enrollment__student_id=student_id)
        else:
            # If no filter, restrict based on role
            user = request.user
            if not user.is_staff:
                if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                    queryset = queryset.filter(enrollment__student=user.student_profile)
                elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                    queryset = queryset.filter(teacher=user.teacher_profile)
                elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                    child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                    queryset = queryset.filter(enrollment__student_id__in=child_ids)
                else:
                    return Response({
                        "status": False,
                        "message": "Permission denied.",
                        "data": None
                    }, status=status.HTTP_403_FORBIDDEN)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, SubjectEnrollmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Subject enrollments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Enrollments - Subject Enrollments"],
        request=SubjectEnrollmentCreateSerializer,
        responses={201: SubjectEnrollmentCreateResponseSerializer, 400: SubjectEnrollmentCreateResponseSerializer, 403: SubjectEnrollmentCreateResponseSerializer},
        description="Enroll a student in a subject (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_subject_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = SubjectEnrollmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            subject_enrollment = serializer.save()
            return Response({
                "status": True,
                "message": "Subject enrollment created.",
                "data": {
                    "id": subject_enrollment.id,
                    "enrollment": subject_enrollment.enrollment.id,
                    "subject": subject_enrollment.subject.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SubjectEnrollmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, subject_enrollment_id):
        try:
            return SubjectEnrollment.objects.select_related('enrollment', 'subject', 'teacher').get(id=subject_enrollment_id)
        except SubjectEnrollment.DoesNotExist:
            return None

    @extend_schema(
        tags=["Enrollments - Subject Enrollments"],
        responses={200: SubjectEnrollmentDetailResponseSerializer, 404: SubjectEnrollmentDetailResponseSerializer, 403: SubjectEnrollmentDetailResponseSerializer},
        description="Retrieve a single subject enrollment by ID."
    )
    def get(self, request, subject_enrollment_id):
        subject_enrollment = self.get_object(subject_enrollment_id)
        if not subject_enrollment:
            return Response({
                "status": False,
                "message": "Subject enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_subject_enrollment(request.user, subject_enrollment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = SubjectEnrollmentDisplaySerializer(subject_enrollment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Subject enrollment retrieved.",
            "data": {"subject_enrollment": data}
        })

    @extend_schema(
        tags=["Enrollments - Subject Enrollments"],
        request=SubjectEnrollmentUpdateSerializer,
        responses={200: SubjectEnrollmentUpdateResponseSerializer, 400: SubjectEnrollmentUpdateResponseSerializer, 403: SubjectEnrollmentUpdateResponseSerializer},
        description="Update a subject enrollment (e.g., assign teacher, update grade)."
    )
    @transaction.atomic
    def put(self, request, subject_enrollment_id):
        return self._update(request, subject_enrollment_id, partial=False)

    @extend_schema(
        tags=["Enrollments - Subject Enrollments"],
        request=SubjectEnrollmentUpdateSerializer,
        responses={200: SubjectEnrollmentUpdateResponseSerializer, 400: SubjectEnrollmentUpdateResponseSerializer, 403: SubjectEnrollmentUpdateResponseSerializer},
        description="Partially update a subject enrollment."
    )
    @transaction.atomic
    def patch(self, request, subject_enrollment_id):
        return self._update(request, subject_enrollment_id, partial=True)

    def _update(self, request, subject_enrollment_id, partial):
        if not can_manage_subject_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        subject_enrollment = self.get_object(subject_enrollment_id)
        if not subject_enrollment:
            return Response({
                "status": False,
                "message": "Subject enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = SubjectEnrollmentUpdateSerializer(subject_enrollment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = SubjectEnrollmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Subject enrollment updated.",
                "data": {"subject_enrollment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Enrollments - Subject Enrollments"],
        responses={200: SubjectEnrollmentDeleteResponseSerializer, 403: SubjectEnrollmentDeleteResponseSerializer, 404: SubjectEnrollmentDeleteResponseSerializer},
        description="Delete a subject enrollment (admin/registrar only)."
    )
    @transaction.atomic
    def delete(self, request, subject_enrollment_id):
        if not can_manage_subject_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        subject_enrollment = self.get_object(subject_enrollment_id)
        if not subject_enrollment:
            return Response({
                "status": False,
                "message": "Subject enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = SubjectEnrollmentService.delete_subject_enrollment(subject_enrollment)
        if success:
            return Response({
                "status": True,
                "message": "Subject enrollment deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete subject enrollment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubjectEnrollmentDropView(APIView):
    permission_classes = [IsAuthenticated]

    class DropSerializer(serializers.Serializer):
        reason = serializers.CharField()
        drop_date = serializers.DateField(required=False)

    @extend_schema(
        tags=["Enrollments - Subject Enrollments"],
        request=DropSerializer,
        responses={200: SubjectEnrollmentDropResponseSerializer, 400: SubjectEnrollmentDropResponseSerializer, 403: SubjectEnrollmentDropResponseSerializer},
        description="Drop a student from a subject (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request, subject_enrollment_id):
        if not can_manage_subject_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        subject_enrollment = SubjectEnrollmentService.get_subject_enrollment_by_id(subject_enrollment_id)
        if not subject_enrollment:
            return Response({
                "status": False,
                "message": "Subject enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.DropSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        reason = serializer.validated_data['reason']
        drop_date = serializer.validated_data.get('drop_date')
        updated = SubjectEnrollmentService.drop_subject(subject_enrollment, reason, drop_date)
        data = SubjectEnrollmentDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Subject dropped.",
            "data": {"subject_enrollment": data}
        })