import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from teachers.models import TeachingAssignment
from teachers.serializers.teaching_assignment import (
    TeachingAssignmentMinimalSerializer,
    TeachingAssignmentCreateSerializer,
    TeachingAssignmentUpdateSerializer,
    TeachingAssignmentDisplaySerializer,
)
from teachers.services.teaching_assignment import TeachingAssignmentService

logger = logging.getLogger(__name__)

def can_view_assignment(user, assignment):
    if user.is_staff:
        return True
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        return assignment.teacher == user.teacher_profile
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return assignment.section.enrollments.filter(student=user.student_profile).exists()
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        child_ids = user.parent_profile.students.values_list('student_id', flat=True)
        return assignment.section.enrollments.filter(student_id__in=child_ids).exists()
    return False

def can_manage_assignment(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TeachingAssignmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    teacher = serializers.IntegerField()
    section = serializers.IntegerField()
    subject = serializers.IntegerField()
    academic_year = serializers.IntegerField()

class TeachingAssignmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeachingAssignmentCreateResponseData(allow_null=True)

class TeachingAssignmentUpdateResponseData(serializers.Serializer):
    assignment = TeachingAssignmentDisplaySerializer()

class TeachingAssignmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeachingAssignmentUpdateResponseData(allow_null=True)

class TeachingAssignmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TeachingAssignmentDetailResponseData(serializers.Serializer):
    assignment = TeachingAssignmentDisplaySerializer()

class TeachingAssignmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeachingAssignmentDetailResponseData(allow_null=True)

class TeachingAssignmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TeachingAssignmentMinimalSerializer(many=True)

class TeachingAssignmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeachingAssignmentListResponseData()

class TeachingAssignmentLoadResponseData(serializers.Serializer):
    total_assignments = serializers.IntegerField()
    unique_subjects = serializers.IntegerField()
    unique_sections = serializers.IntegerField()

class TeachingAssignmentLoadResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TeachingAssignmentLoadResponseData()

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

class TeachingAssignmentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Teachers - Assignments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="teacher_id", type=int, description="Filter by teacher ID", required=False),
            OpenApiParameter(name="section_id", type=int, description="Filter by section ID", required=False),
            OpenApiParameter(name="subject_id", type=int, description="Filter by subject ID", required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year", required=False),
        ],
        responses={200: TeachingAssignmentListResponseSerializer},
        description="List teaching assignments (filtered by role)."
    )
    def get(self, request):
        user = request.user
        teacher_id = request.query_params.get("teacher_id")
        section_id = request.query_params.get("section_id")
        subject_id = request.query_params.get("subject_id")
        academic_year_id = request.query_params.get("academic_year_id")

        if user.is_staff or can_manage_assignment(user):
            queryset = TeachingAssignment.objects.all().select_related('teacher', 'section', 'subject', 'academic_year', 'term')
        else:
            if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                queryset = TeachingAssignment.objects.filter(teacher=user.teacher_profile)
            elif user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                # Get assignments for sections the student is enrolled in
                from enrollments.models import Enrollment
                sections = Enrollment.objects.filter(student=user.student_profile, status='ENR').values_list('section_id', flat=True)
                queryset = TeachingAssignment.objects.filter(section_id__in=sections, is_active=True)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                from enrollments.models import Enrollment
                sections = Enrollment.objects.filter(student_id__in=child_ids, status='ENR').values_list('section_id', flat=True)
                queryset = TeachingAssignment.objects.filter(section_id__in=sections, is_active=True)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)

        queryset = queryset.order_by('academic_year__start_date', 'section__name')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, TeachingAssignmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Teaching assignments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Teachers - Assignments"],
        request=TeachingAssignmentCreateSerializer,
        responses={201: TeachingAssignmentCreateResponseSerializer, 400: TeachingAssignmentCreateResponseSerializer, 403: TeachingAssignmentCreateResponseSerializer},
        description="Create a teaching assignment (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_assignment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = TeachingAssignmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            assignment = serializer.save()
            return Response({
                "status": True,
                "message": "Teaching assignment created.",
                "data": {
                    "id": assignment.id,
                    "teacher": assignment.teacher.id,
                    "section": assignment.section.id,
                    "subject": assignment.subject.id,
                    "academic_year": assignment.academic_year.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeachingAssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, assignment_id):
        try:
            return TeachingAssignment.objects.select_related('teacher', 'section', 'subject', 'academic_year', 'term').get(id=assignment_id)
        except TeachingAssignment.DoesNotExist:
            return None

    @extend_schema(
        tags=["Teachers - Assignments"],
        responses={200: TeachingAssignmentDetailResponseSerializer, 404: TeachingAssignmentDetailResponseSerializer, 403: TeachingAssignmentDetailResponseSerializer},
        description="Retrieve a single teaching assignment by ID."
    )
    def get(self, request, assignment_id):
        assignment = self.get_object(assignment_id)
        if not assignment:
            return Response({
                "status": False,
                "message": "Assignment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_assignment(request.user, assignment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = TeachingAssignmentDisplaySerializer(assignment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Assignment retrieved.",
            "data": {"assignment": data}
        })

    @extend_schema(
        tags=["Teachers - Assignments"],
        request=TeachingAssignmentUpdateSerializer,
        responses={200: TeachingAssignmentUpdateResponseSerializer, 400: TeachingAssignmentUpdateResponseSerializer, 403: TeachingAssignmentUpdateResponseSerializer},
        description="Update a teaching assignment (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, assignment_id):
        return self._update(request, assignment_id, partial=False)

    @extend_schema(
        tags=["Teachers - Assignments"],
        request=TeachingAssignmentUpdateSerializer,
        responses={200: TeachingAssignmentUpdateResponseSerializer, 400: TeachingAssignmentUpdateResponseSerializer, 403: TeachingAssignmentUpdateResponseSerializer},
        description="Partially update a teaching assignment."
    )
    @transaction.atomic
    def patch(self, request, assignment_id):
        return self._update(request, assignment_id, partial=True)

    def _update(self, request, assignment_id, partial):
        if not can_manage_assignment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        assignment = self.get_object(assignment_id)
        if not assignment:
            return Response({
                "status": False,
                "message": "Assignment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TeachingAssignmentUpdateSerializer(assignment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = TeachingAssignmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Assignment updated.",
                "data": {"assignment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Teachers - Assignments"],
        responses={200: TeachingAssignmentDeleteResponseSerializer, 403: TeachingAssignmentDeleteResponseSerializer, 404: TeachingAssignmentDeleteResponseSerializer},
        description="Delete a teaching assignment (admin only)."
    )
    @transaction.atomic
    def delete(self, request, assignment_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        assignment = self.get_object(assignment_id)
        if not assignment:
            return Response({
                "status": False,
                "message": "Assignment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = TeachingAssignmentService.delete_assignment(assignment)
        if success:
            return Response({
                "status": True,
                "message": "Assignment deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete assignment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherLoadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Teachers - Assignments"],
        parameters=[
            OpenApiParameter(name="teacher_id", type=int, description="Teacher ID", required=True),
            OpenApiParameter(name="academic_year_id", type=int, description="Academic year ID", required=True),
        ],
        responses={200: TeachingAssignmentLoadResponseSerializer, 403: TeachingAssignmentLoadResponseSerializer, 404: TeachingAssignmentLoadResponseSerializer},
        description="Get teacher's load summary (admin/HR only)."
    )
    def get(self, request):
        if not can_manage_assignment(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        teacher_id = request.query_params.get("teacher_id")
        academic_year_id = request.query_params.get("academic_year_id")
        if not teacher_id or not academic_year_id:
            return Response({
                "status": False,
                "message": "teacher_id and academic_year_id parameters required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        load = TeachingAssignmentService.get_teacher_load(teacher_id, academic_year_id)
        return Response({
            "status": True,
            "message": "Teacher load retrieved.",
            "data": load
        })