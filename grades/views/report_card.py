import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from grades.models import ReportCard
from grades.serializers.report_card import (
    ReportCardMinimalSerializer,
    ReportCardCreateSerializer,
    ReportCardUpdateSerializer,
    ReportCardDisplaySerializer,
)
from grades.services.report_card import ReportCardService

logger = logging.getLogger(__name__)

def can_view_report_card(user, report_card):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return report_card.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return report_card.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
        # Teacher can see report cards for students in sections they teach
        teacher = user.teacher_profile
        sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
        from enrollments.models import Enrollment
        student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
        return report_card.student_id in student_ids
    return False

def can_manage_report_card(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'TEACHER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ReportCardCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    academic_year = serializers.IntegerField()
    term = serializers.IntegerField()
    gpa = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

class ReportCardCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportCardCreateResponseData(allow_null=True)

class ReportCardUpdateResponseData(serializers.Serializer):
    report_card = ReportCardDisplaySerializer()

class ReportCardUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportCardUpdateResponseData(allow_null=True)

class ReportCardDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ReportCardDetailResponseData(serializers.Serializer):
    report_card = ReportCardDisplaySerializer()

class ReportCardDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportCardDetailResponseData(allow_null=True)

class ReportCardListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ReportCardMinimalSerializer(many=True)

class ReportCardListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReportCardListResponseData()

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

class ReportCardListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Report Cards"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year ID", required=False),
            OpenApiParameter(name="term_id", type=int, description="Filter by term ID", required=False),
        ],
        responses={200: ReportCardListResponseSerializer},
        description="List report cards (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        academic_year_id = request.query_params.get("academic_year_id")
        term_id = request.query_params.get("term_id")

        if user.is_staff or can_manage_report_card(user):
            queryset = ReportCard.objects.all().select_related('student', 'academic_year', 'term', 'signed_by')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = ReportCard.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = ReportCard.objects.filter(student_id__in=child_ids)
            elif user.role == 'TEACHER' and hasattr(user, 'teacher_profile'):
                # Teacher sees report cards for students in their sections
                teacher = user.teacher_profile
                sections = teacher.assignments.filter(is_active=True).values_list('section_id', flat=True)
                from enrollments.models import Enrollment
                student_ids = Enrollment.objects.filter(section_id__in=sections, status='ENR').values_list('student_id', flat=True)
                queryset = ReportCard.objects.filter(student_id__in=student_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if term_id:
            queryset = queryset.filter(term_id=term_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ReportCardMinimalSerializer)
        return Response({
            "status": True,
            "message": "Report cards retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Grades - Report Cards"],
        request=ReportCardCreateSerializer,
        responses={201: ReportCardCreateResponseSerializer, 400: ReportCardCreateResponseSerializer, 403: ReportCardCreateResponseSerializer},
        description="Create a report card (teacher/admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_report_card(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportCardCreateSerializer(data=request.data)
        if serializer.is_valid():
            report_card = serializer.save()
            return Response({
                "status": True,
                "message": "Report card created.",
                "data": {
                    "id": report_card.id,
                    "student": report_card.student.id,
                    "academic_year": report_card.academic_year.id,
                    "term": report_card.term.id,
                    "gpa": report_card.gpa,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReportCardDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, report_id):
        try:
            return ReportCard.objects.select_related('student', 'academic_year', 'term', 'signed_by').get(id=report_id)
        except ReportCard.DoesNotExist:
            return None

    @extend_schema(
        tags=["Grades - Report Cards"],
        responses={200: ReportCardDetailResponseSerializer, 404: ReportCardDetailResponseSerializer, 403: ReportCardDetailResponseSerializer},
        description="Retrieve a single report card by ID."
    )
    def get(self, request, report_id):
        report_card = self.get_object(report_id)
        if not report_card:
            return Response({
                "status": False,
                "message": "Report card not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_report_card(request.user, report_card):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ReportCardDisplaySerializer(report_card, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Report card retrieved.",
            "data": {"report_card": data}
        })

    @extend_schema(
        tags=["Grades - Report Cards"],
        request=ReportCardUpdateSerializer,
        responses={200: ReportCardUpdateResponseSerializer, 400: ReportCardUpdateResponseSerializer, 403: ReportCardUpdateResponseSerializer},
        description="Update a report card (teacher/admin only)."
    )
    @transaction.atomic
    def put(self, request, report_id):
        return self._update(request, report_id, partial=False)

    @extend_schema(
        tags=["Grades - Report Cards"],
        request=ReportCardUpdateSerializer,
        responses={200: ReportCardUpdateResponseSerializer, 400: ReportCardUpdateResponseSerializer, 403: ReportCardUpdateResponseSerializer},
        description="Partially update a report card."
    )
    @transaction.atomic
    def patch(self, request, report_id):
        return self._update(request, report_id, partial=True)

    def _update(self, request, report_id, partial):
        if not can_manage_report_card(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report_card = self.get_object(report_id)
        if not report_card:
            return Response({
                "status": False,
                "message": "Report card not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ReportCardUpdateSerializer(report_card, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ReportCardDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Report card updated.",
                "data": {"report_card": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Grades - Report Cards"],
        responses={200: ReportCardDeleteResponseSerializer, 403: ReportCardDeleteResponseSerializer, 404: ReportCardDeleteResponseSerializer},
        description="Delete a report card (admin only)."
    )
    @transaction.atomic
    def delete(self, request, report_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report_card = self.get_object(report_id)
        if not report_card:
            return Response({
                "status": False,
                "message": "Report card not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ReportCardService.delete_report_card(report_card)
        if success:
            return Response({
                "status": True,
                "message": "Report card deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete report card.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportCardComputeGPAView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Grades - Report Cards"],
        responses={200: ReportCardUpdateResponseSerializer, 403: ReportCardUpdateResponseSerializer, 404: ReportCardUpdateResponseSerializer},
        description="Compute GPA from grades and update report card (teacher/admin only)."
    )
    @transaction.atomic
    def post(self, request, report_id):
        if not can_manage_report_card(request.user):
            return Response({
                "status": False,
                "message": "Teacher or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        report_card = ReportCardService.get_report_card_by_id(report_id)
        if not report_card:
            return Response({
                "status": False,
                "message": "Report card not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        gpa = ReportCardService.compute_gpa_from_grades(
            report_card.student.id,
            report_card.academic_year.id,
            report_card.term.id
        )
        updated = ReportCardService.update_report_card(report_card, {'gpa': gpa})
        data = ReportCardDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "GPA computed and report card updated.",
            "data": {"report_card": data}
        })