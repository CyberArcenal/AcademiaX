import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from fees.models import Scholarship
from fees.serializers.scholarship import (
    ScholarshipMinimalSerializer,
    ScholarshipCreateSerializer,
    ScholarshipUpdateSerializer,
    ScholarshipDisplaySerializer,
)
from fees.services.scholarship import ScholarshipService

logger = logging.getLogger(__name__)

def can_view_scholarship(user, scholarship):
    if user.is_staff:
        return True
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return scholarship.student == user.student_profile
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return scholarship.student in [sp.student for sp in user.parent_profile.students.all()]
    if user.role in ['ADMIN', 'ACCOUNTING']:
        return True
    return False

def can_manage_scholarship(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ScholarshipCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    discount = serializers.IntegerField()
    scholarship_type = serializers.CharField()

class ScholarshipCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScholarshipCreateResponseData(allow_null=True)

class ScholarshipUpdateResponseData(serializers.Serializer):
    scholarship = ScholarshipDisplaySerializer()

class ScholarshipUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScholarshipUpdateResponseData(allow_null=True)

class ScholarshipDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ScholarshipDetailResponseData(serializers.Serializer):
    scholarship = ScholarshipDisplaySerializer()

class ScholarshipDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScholarshipDetailResponseData(allow_null=True)

class ScholarshipListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ScholarshipMinimalSerializer(many=True)

class ScholarshipListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ScholarshipListResponseData()

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

class ScholarshipListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Fees - Scholarships"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active scholarships (not expired)", required=False),
        ],
        responses={200: ScholarshipListResponseSerializer},
        description="List scholarships (students/parents see their own, staff see all)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        active_only = request.query_params.get("active_only", "false").lower() == "true"

        if user.is_staff or can_manage_scholarship(user):
            queryset = Scholarship.objects.all().select_related('student', 'discount', 'approved_by')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = Scholarship.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                child_ids = user.parent_profile.students.values_list('student_id', flat=True)
                queryset = Scholarship.objects.filter(student_id__in=child_ids)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if active_only:
            from datetime import date
            queryset = queryset.filter(expiry_date__gte=date.today())

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ScholarshipMinimalSerializer)
        return Response({
            "status": True,
            "message": "Scholarships retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Fees - Scholarships"],
        request=ScholarshipCreateSerializer,
        responses={201: ScholarshipCreateResponseSerializer, 400: ScholarshipCreateResponseSerializer, 403: ScholarshipCreateResponseSerializer},
        description="Award a scholarship to a student (admin/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_scholarship(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Add approved_by from current user
        data = request.data.copy()
        data['approved_by_id'] = request.user.id
        serializer = ScholarshipCreateSerializer(data=data)
        if serializer.is_valid():
            scholarship = serializer.save()
            return Response({
                "status": True,
                "message": "Scholarship awarded.",
                "data": {
                    "id": scholarship.id,
                    "student": scholarship.student.id,
                    "discount": scholarship.discount.id,
                    "scholarship_type": scholarship.scholarship_type,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ScholarshipDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, scholarship_id):
        try:
            return Scholarship.objects.select_related('student', 'discount', 'approved_by').get(id=scholarship_id)
        except Scholarship.DoesNotExist:
            return None

    @extend_schema(
        tags=["Fees - Scholarships"],
        responses={200: ScholarshipDetailResponseSerializer, 404: ScholarshipDetailResponseSerializer, 403: ScholarshipDetailResponseSerializer},
        description="Retrieve a single scholarship by ID."
    )
    def get(self, request, scholarship_id):
        scholarship = self.get_object(scholarship_id)
        if not scholarship:
            return Response({
                "status": False,
                "message": "Scholarship not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_scholarship(request.user, scholarship):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ScholarshipDisplaySerializer(scholarship, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Scholarship retrieved.",
            "data": {"scholarship": data}
        })

    @extend_schema(
        tags=["Fees - Scholarships"],
        request=ScholarshipUpdateSerializer,
        responses={200: ScholarshipUpdateResponseSerializer, 400: ScholarshipUpdateResponseSerializer, 403: ScholarshipUpdateResponseSerializer},
        description="Update a scholarship (admin/accounting only)."
    )
    @transaction.atomic
    def put(self, request, scholarship_id):
        return self._update(request, scholarship_id, partial=False)

    @extend_schema(
        tags=["Fees - Scholarships"],
        request=ScholarshipUpdateSerializer,
        responses={200: ScholarshipUpdateResponseSerializer, 400: ScholarshipUpdateResponseSerializer, 403: ScholarshipUpdateResponseSerializer},
        description="Partially update a scholarship."
    )
    @transaction.atomic
    def patch(self, request, scholarship_id):
        return self._update(request, scholarship_id, partial=True)

    def _update(self, request, scholarship_id, partial):
        if not can_manage_scholarship(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        scholarship = self.get_object(scholarship_id)
        if not scholarship:
            return Response({
                "status": False,
                "message": "Scholarship not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ScholarshipUpdateSerializer(scholarship, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ScholarshipDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Scholarship updated.",
                "data": {"scholarship": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Fees - Scholarships"],
        responses={200: ScholarshipDeleteResponseSerializer, 403: ScholarshipDeleteResponseSerializer, 404: ScholarshipDeleteResponseSerializer},
        description="Delete a scholarship (admin/accounting only)."
    )
    @transaction.atomic
    def delete(self, request, scholarship_id):
        if not can_manage_scholarship(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        scholarship = self.get_object(scholarship_id)
        if not scholarship:
            return Response({
                "status": False,
                "message": "Scholarship not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ScholarshipService.delete_scholarship(scholarship)
        if success:
            return Response({
                "status": True,
                "message": "Scholarship deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete scholarship.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScholarshipRenewView(APIView):
    permission_classes = [IsAuthenticated]

    class RenewSerializer(serializers.Serializer):
        new_expiry_date = serializers.DateField()

    @extend_schema(
        tags=["Fees - Scholarships"],
        request=RenewSerializer,
        responses={200: ScholarshipUpdateResponseSerializer, 400: ScholarshipUpdateResponseSerializer, 403: ScholarshipUpdateResponseSerializer},
        description="Renew a scholarship (extend expiry date)."
    )
    @transaction.atomic
    def post(self, request, scholarship_id):
        if not can_manage_scholarship(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        scholarship = ScholarshipService.get_scholarship_by_id(scholarship_id)
        if not scholarship:
            return Response({
                "status": False,
                "message": "Scholarship not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.RenewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = ScholarshipService.renew_scholarship(scholarship, serializer.validated_data['new_expiry_date'])
        data = ScholarshipDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Scholarship renewed.",
            "data": {"scholarship": data}
        })