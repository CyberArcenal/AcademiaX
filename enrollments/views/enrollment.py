import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from enrollments.models import Enrollment
from enrollments.serializers.enrollment import (
    EnrollmentMinimalSerializer,
    EnrollmentCreateSerializer,
    EnrollmentUpdateSerializer,
    EnrollmentDisplaySerializer,
)
from enrollments.services.enrollment import EnrollmentService

logger = logging.getLogger(__name__)

def can_view_enrollment(user, enrollment):
    if user.is_staff:
        return True
    if user.role == 'TEACHER':
        # Teachers can see enrollments in their sections
        return enrollment.section.teacher_assignments.filter(teacher__user=user, is_active=True).exists()
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return enrollment.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        # Parent can see their children's enrollments
        return enrollment.student in [sp.student for sp in user.parent_profile.students.all()]
    return False

def can_manage_enrollment(user):
    # Staff, Registrar, or Admin can manage enrollments
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class EnrollmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    academic_year = serializers.IntegerField()
    status = serializers.CharField()

class EnrollmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentCreateResponseData(allow_null=True)

class EnrollmentUpdateResponseData(serializers.Serializer):
    enrollment = EnrollmentDisplaySerializer()

class EnrollmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentUpdateResponseData(allow_null=True)

class EnrollmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EnrollmentDetailResponseData(serializers.Serializer):
    enrollment = EnrollmentDisplaySerializer()

class EnrollmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentDetailResponseData(allow_null=True)

class EnrollmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EnrollmentMinimalSerializer(many=True)

class EnrollmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentListResponseData()

class EnrollmentTransferResponseData(serializers.Serializer):
    enrollment = EnrollmentDisplaySerializer()

class EnrollmentTransferResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EnrollmentTransferResponseData()

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

class EnrollmentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Enrollments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year", required=False),
            OpenApiParameter(name="section_id", type=int, description="Filter by section", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by status", required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
        ],
        responses={200: EnrollmentListResponseSerializer},
        description="List enrollments (filtered by role)."
    )
    def get(self, request):
        user = request.user
        queryset = Enrollment.objects.all().select_related('student', 'academic_year', 'grade_level', 'section', 'processed_by')
        if not user.is_staff:
            if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                # Teachers see enrollments in their sections
                teacher = user.teacher_profile
                section_ids = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                queryset = queryset.filter(section_id__in=section_ids)
            elif user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = queryset.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                # Parent sees children's enrollments
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = queryset.filter(student_id__in=child_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        academic_year_id = request.query_params.get("academic_year_id")
        section_id = request.query_params.get("section_id")
        status_filter = request.query_params.get("status")
        student_id = request.query_params.get("student_id")

        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, EnrollmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Enrollments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Enrollments"],
        request=EnrollmentCreateSerializer,
        responses={201: EnrollmentCreateResponseSerializer, 400: EnrollmentCreateResponseSerializer, 403: EnrollmentCreateResponseSerializer},
        description="Create a new enrollment (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = EnrollmentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            enrollment = serializer.save()
            return Response({
                "status": True,
                "message": "Enrollment created.",
                "data": {
                    "id": enrollment.id,
                    "student": enrollment.student.id,
                    "academic_year": enrollment.academic_year.id,
                    "status": enrollment.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EnrollmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, enrollment_id):
        try:
            return Enrollment.objects.select_related('student', 'academic_year', 'grade_level', 'section', 'processed_by').get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return None

    @extend_schema(
        tags=["Enrollments"],
        responses={200: EnrollmentDetailResponseSerializer, 404: EnrollmentDetailResponseSerializer, 403: EnrollmentDetailResponseSerializer},
        description="Retrieve a single enrollment by ID."
    )
    def get(self, request, enrollment_id):
        enrollment = self.get_object(enrollment_id)
        if not enrollment:
            return Response({
                "status": False,
                "message": "Enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_enrollment(request.user, enrollment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = EnrollmentDisplaySerializer(enrollment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Enrollment retrieved.",
            "data": {"enrollment": data}
        })

    @extend_schema(
        tags=["Enrollments"],
        request=EnrollmentUpdateSerializer,
        responses={200: EnrollmentUpdateResponseSerializer, 400: EnrollmentUpdateResponseSerializer, 403: EnrollmentUpdateResponseSerializer},
        description="Update an enrollment (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, enrollment_id):
        return self._update(request, enrollment_id, partial=False)

    @extend_schema(
        tags=["Enrollments"],
        request=EnrollmentUpdateSerializer,
        responses={200: EnrollmentUpdateResponseSerializer, 400: EnrollmentUpdateResponseSerializer, 403: EnrollmentUpdateResponseSerializer},
        description="Partially update an enrollment."
    )
    @transaction.atomic
    def patch(self, request, enrollment_id):
        return self._update(request, enrollment_id, partial=True)

    def _update(self, request, enrollment_id, partial):
        if not can_manage_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        enrollment = self.get_object(enrollment_id)
        if not enrollment:
            return Response({
                "status": False,
                "message": "Enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = EnrollmentUpdateSerializer(enrollment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EnrollmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Enrollment updated.",
                "data": {"enrollment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Enrollments"],
        responses={200: EnrollmentDeleteResponseSerializer, 403: EnrollmentDeleteResponseSerializer, 404: EnrollmentDeleteResponseSerializer},
        description="Delete an enrollment (soft delete, admin/registrar only)."
    )
    @transaction.atomic
    def delete(self, request, enrollment_id):
        if not can_manage_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        enrollment = self.get_object(enrollment_id)
        if not enrollment:
            return Response({
                "status": False,
                "message": "Enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = EnrollmentService.delete_enrollment(enrollment)
        if success:
            return Response({
                "status": True,
                "message": "Enrollment deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete enrollment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EnrollmentTransferSectionView(APIView):
    permission_classes = [IsAuthenticated]

    class TransferSerializer(serializers.Serializer):
        new_section_id = serializers.IntegerField()

    @extend_schema(
        tags=["Enrollments"],
        request=TransferSerializer,
        responses={200: EnrollmentTransferResponseSerializer, 400: EnrollmentTransferResponseSerializer, 403: EnrollmentTransferResponseSerializer},
        description="Transfer a student to a different section (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request, enrollment_id):
        if not can_manage_enrollment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        enrollment = EnrollmentService.get_enrollment_by_id(enrollment_id)
        if not enrollment:
            return Response({
                "status": False,
                "message": "Enrollment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.TransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        from classes.services.section import SectionService
        new_section = SectionService.get_section_by_id(serializer.validated_data['new_section_id'])
        if not new_section:
            return Response({
                "status": False,
                "message": "New section not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = EnrollmentService.transfer_section(enrollment, new_section)
        data = EnrollmentDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Student transferred to new section.",
            "data": {"enrollment": data}
        })