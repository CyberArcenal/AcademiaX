import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from alumni.models import Employment
from alumni.serializers.employment import (
    EmploymentMinimalSerializer,
    EmploymentCreateSerializer,
    EmploymentUpdateSerializer,
    EmploymentDisplaySerializer,
)
from alumni.services.employment import EmploymentService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class EmploymentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    alumni = serializers.IntegerField()
    job_title = serializers.CharField()

class EmploymentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmploymentCreateResponseData(allow_null=True)

class EmploymentUpdateResponseData(serializers.Serializer):
    employment = EmploymentDisplaySerializer()

class EmploymentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmploymentUpdateResponseData(allow_null=True)

class EmploymentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EmploymentDetailResponseData(serializers.Serializer):
    employment = EmploymentDisplaySerializer()

class EmploymentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmploymentDetailResponseData(allow_null=True)

class EmploymentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EmploymentMinimalSerializer(many=True)

class EmploymentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmploymentListResponseData()

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

class EmploymentListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni - Employment"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="alumni_id", type=int, description="Filter by alumni ID", required=False),
        ],
        responses={200: EmploymentListResponseSerializer},
        description="List employment records, optionally filtered by alumni."
    )
    def get(self, request):
        alumni_id = request.query_params.get("alumni_id")
        if alumni_id:
            employments = EmploymentService.get_employments_by_alumni(alumni_id)
        else:
            employments = Employment.objects.all().select_related('alumni').order_by('-start_date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(employments, request)
        data = wrap_paginated_data(paginator, page, request, EmploymentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Employment records retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Alumni - Employment"],
        request=EmploymentCreateSerializer,
        responses={201: EmploymentCreateResponseSerializer, 400: EmploymentCreateResponseSerializer},
        description="Create a new employment record."
    )
    @transaction.atomic
    def post(self, request):
        serializer = EmploymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            employment = serializer.save()
            return Response({
                "status": True,
                "message": "Employment record created.",
                "data": {
                    "id": employment.id,
                    "alumni": employment.alumni.id,
                    "job_title": employment.job_title,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmploymentDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, employment_id):
        return EmploymentService.get_employment_by_id(employment_id)

    @extend_schema(
        tags=["Alumni - Employment"],
        responses={200: EmploymentDetailResponseSerializer, 404: EmploymentDetailResponseSerializer},
        description="Retrieve a single employment record by ID."
    )
    def get(self, request, employment_id):
        employment = self.get_object(employment_id)
        if not employment:
            return Response({
                "status": False,
                "message": "Employment record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = EmploymentDisplaySerializer(employment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Employment record retrieved.",
            "data": {"employment": data}
        })

    @extend_schema(
        tags=["Alumni - Employment"],
        request=EmploymentUpdateSerializer,
        responses={200: EmploymentUpdateResponseSerializer, 400: EmploymentUpdateResponseSerializer, 403: EmploymentUpdateResponseSerializer},
        description="Update an employment record."
    )
    @transaction.atomic
    def put(self, request, employment_id):
        return self._update(request, employment_id, partial=False)

    @extend_schema(
        tags=["Alumni - Employment"],
        request=EmploymentUpdateSerializer,
        responses={200: EmploymentUpdateResponseSerializer, 400: EmploymentUpdateResponseSerializer, 403: EmploymentUpdateResponseSerializer},
        description="Partially update an employment record."
    )
    @transaction.atomic
    def patch(self, request, employment_id):
        return self._update(request, employment_id, partial=True)

    def _update(self, request, employment_id, partial):
        employment = self.get_object(employment_id)
        if not employment:
            return Response({
                "status": False,
                "message": "Employment record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Allow only staff or the alumni owner (via alumni.user)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if not (user.is_staff or (employment.alumni.user and user == employment.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = EmploymentUpdateSerializer(employment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EmploymentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Employment record updated.",
                "data": {"employment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Alumni - Employment"],
        responses={200: EmploymentDeleteResponseSerializer, 403: EmploymentDeleteResponseSerializer, 404: EmploymentDeleteResponseSerializer},
        description="Delete an employment record (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, employment_id):
        employment = self.get_object(employment_id)
        if not employment:
            return Response({
                "status": False,
                "message": "Employment record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not (user.is_staff or (employment.alumni.user and user == employment.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = EmploymentService.delete_employment(employment)
        if success:
            return Response({
                "status": True,
                "message": "Employment record deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete employment record.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)