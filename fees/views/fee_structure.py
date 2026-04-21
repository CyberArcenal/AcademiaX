import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from fees.models import FeeStructure
from fees.serializers.fee_structure import (
    FeeStructureMinimalSerializer,
    FeeStructureCreateSerializer,
    FeeStructureUpdateSerializer,
    FeeStructureDisplaySerializer,
)
from fees.services.fee_structure import FeeStructureService

logger = logging.getLogger(__name__)

def can_manage_fee_structure(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class FeeStructureCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()

class FeeStructureCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeStructureCreateResponseData(allow_null=True)

class FeeStructureUpdateResponseData(serializers.Serializer):
    fee_structure = FeeStructureDisplaySerializer()

class FeeStructureUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeStructureUpdateResponseData(allow_null=True)

class FeeStructureDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class FeeStructureDetailResponseData(serializers.Serializer):
    fee_structure = FeeStructureDisplaySerializer()

class FeeStructureDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeStructureDetailResponseData(allow_null=True)

class FeeStructureListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = FeeStructureMinimalSerializer(many=True)

class FeeStructureListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FeeStructureListResponseData()

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

class FeeStructureListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Fees - Fee Structures"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year", required=False),
            OpenApiParameter(name="grade_level_id", type=int, description="Filter by grade level", required=False),
        ],
        responses={200: FeeStructureListResponseSerializer},
        description="List fee structures (public)."
    )
    def get(self, request):
        academic_year_id = request.query_params.get("academic_year_id")
        grade_level_id = request.query_params.get("grade_level_id")
        queryset = FeeStructure.objects.all().select_related('academic_year', 'grade_level', 'academic_program')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if grade_level_id:
            queryset = queryset.filter(grade_level_id=grade_level_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, FeeStructureMinimalSerializer)
        return Response({
            "status": True,
            "message": "Fee structures retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Fees - Fee Structures"],
        request=FeeStructureCreateSerializer,
        responses={201: FeeStructureCreateResponseSerializer, 400: FeeStructureCreateResponseSerializer, 403: FeeStructureCreateResponseSerializer},
        description="Create a new fee structure (admin/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_fee_structure(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = FeeStructureCreateSerializer(data=request.data)
        if serializer.is_valid():
            fs = serializer.save()
            return Response({
                "status": True,
                "message": "Fee structure created.",
                "data": {
                    "id": fs.id,
                    "name": fs.name,
                    "category": fs.category,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FeeStructureDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, fs_id):
        return FeeStructureService.get_fee_structure_by_id(fs_id)

    @extend_schema(
        tags=["Fees - Fee Structures"],
        responses={200: FeeStructureDetailResponseSerializer, 404: FeeStructureDetailResponseSerializer},
        description="Retrieve a single fee structure by ID."
    )
    def get(self, request, fs_id):
        fs = self.get_object(fs_id)
        if not fs:
            return Response({
                "status": False,
                "message": "Fee structure not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = FeeStructureDisplaySerializer(fs, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Fee structure retrieved.",
            "data": {"fee_structure": data}
        })

    @extend_schema(
        tags=["Fees - Fee Structures"],
        request=FeeStructureUpdateSerializer,
        responses={200: FeeStructureUpdateResponseSerializer, 400: FeeStructureUpdateResponseSerializer, 403: FeeStructureUpdateResponseSerializer},
        description="Update a fee structure (admin/accounting only)."
    )
    @transaction.atomic
    def put(self, request, fs_id):
        return self._update(request, fs_id, partial=False)

    @extend_schema(
        tags=["Fees - Fee Structures"],
        request=FeeStructureUpdateSerializer,
        responses={200: FeeStructureUpdateResponseSerializer, 400: FeeStructureUpdateResponseSerializer, 403: FeeStructureUpdateResponseSerializer},
        description="Partially update a fee structure."
    )
    @transaction.atomic
    def patch(self, request, fs_id):
        return self._update(request, fs_id, partial=True)

    def _update(self, request, fs_id, partial):
        if not can_manage_fee_structure(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        fs = self.get_object(fs_id)
        if not fs:
            return Response({
                "status": False,
                "message": "Fee structure not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = FeeStructureUpdateSerializer(fs, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = FeeStructureDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Fee structure updated.",
                "data": {"fee_structure": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Fees - Fee Structures"],
        responses={200: FeeStructureDeleteResponseSerializer, 403: FeeStructureDeleteResponseSerializer, 404: FeeStructureDeleteResponseSerializer},
        description="Delete a fee structure (admin/accounting only)."
    )
    @transaction.atomic
    def delete(self, request, fs_id):
        if not can_manage_fee_structure(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        fs = self.get_object(fs_id)
        if not fs:
            return Response({
                "status": False,
                "message": "Fee structure not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = FeeStructureService.delete_fee_structure(fs)
        if success:
            return Response({
                "status": True,
                "message": "Fee structure deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete fee structure.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)