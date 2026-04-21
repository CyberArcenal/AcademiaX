import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from fees.models import Discount
from fees.serializers.discount import (
    DiscountMinimalSerializer,
    DiscountCreateSerializer,
    DiscountUpdateSerializer,
    DiscountDisplaySerializer,
)
from fees.services.discount import DiscountService

logger = logging.getLogger(__name__)

def can_manage_discount(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class DiscountCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    discount_type = serializers.CharField()
    value = serializers.DecimalField(max_digits=8, decimal_places=2)

class DiscountCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DiscountCreateResponseData(allow_null=True)

class DiscountUpdateResponseData(serializers.Serializer):
    discount = DiscountDisplaySerializer()

class DiscountUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DiscountUpdateResponseData(allow_null=True)

class DiscountDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class DiscountDetailResponseData(serializers.Serializer):
    discount = DiscountDisplaySerializer()

class DiscountDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DiscountDetailResponseData(allow_null=True)

class DiscountListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = DiscountMinimalSerializer(many=True)

class DiscountListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DiscountListResponseData()

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

class DiscountListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Fees - Discounts"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active discounts", required=False),
        ],
        responses={200: DiscountListResponseSerializer},
        description="List discounts (public)."
    )
    def get(self, request):
        academic_year_id = request.query_params.get("academic_year_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if academic_year_id:
            discounts = DiscountService.get_active_discounts(academic_year_id=academic_year_id) if active_only else Discount.objects.filter(academic_year_id=academic_year_id)
        else:
            discounts = DiscountService.get_active_discounts() if active_only else Discount.objects.all()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(discounts, request)
        data = wrap_paginated_data(paginator, page, request, DiscountMinimalSerializer)
        return Response({
            "status": True,
            "message": "Discounts retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Fees - Discounts"],
        request=DiscountCreateSerializer,
        responses={201: DiscountCreateResponseSerializer, 400: DiscountCreateResponseSerializer, 403: DiscountCreateResponseSerializer},
        description="Create a new discount (admin/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_discount(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = DiscountCreateSerializer(data=request.data)
        if serializer.is_valid():
            discount = serializer.save()
            return Response({
                "status": True,
                "message": "Discount created.",
                "data": {
                    "id": discount.id,
                    "name": discount.name,
                    "discount_type": discount.discount_type,
                    "value": discount.value,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DiscountDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, discount_id):
        return DiscountService.get_discount_by_id(discount_id)

    @extend_schema(
        tags=["Fees - Discounts"],
        responses={200: DiscountDetailResponseSerializer, 404: DiscountDetailResponseSerializer},
        description="Retrieve a single discount by ID."
    )
    def get(self, request, discount_id):
        discount = self.get_object(discount_id)
        if not discount:
            return Response({
                "status": False,
                "message": "Discount not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = DiscountDisplaySerializer(discount, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Discount retrieved.",
            "data": {"discount": data}
        })

    @extend_schema(
        tags=["Fees - Discounts"],
        request=DiscountUpdateSerializer,
        responses={200: DiscountUpdateResponseSerializer, 400: DiscountUpdateResponseSerializer, 403: DiscountUpdateResponseSerializer},
        description="Update a discount (admin/accounting only)."
    )
    @transaction.atomic
    def put(self, request, discount_id):
        return self._update(request, discount_id, partial=False)

    @extend_schema(
        tags=["Fees - Discounts"],
        request=DiscountUpdateSerializer,
        responses={200: DiscountUpdateResponseSerializer, 400: DiscountUpdateResponseSerializer, 403: DiscountUpdateResponseSerializer},
        description="Partially update a discount."
    )
    @transaction.atomic
    def patch(self, request, discount_id):
        return self._update(request, discount_id, partial=True)

    def _update(self, request, discount_id, partial):
        if not can_manage_discount(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        discount = self.get_object(discount_id)
        if not discount:
            return Response({
                "status": False,
                "message": "Discount not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = DiscountUpdateSerializer(discount, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = DiscountDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Discount updated.",
                "data": {"discount": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Fees - Discounts"],
        responses={200: DiscountDeleteResponseSerializer, 403: DiscountDeleteResponseSerializer, 404: DiscountDeleteResponseSerializer},
        description="Delete a discount (admin/accounting only)."
    )
    @transaction.atomic
    def delete(self, request, discount_id):
        if not can_manage_discount(request.user):
            return Response({
                "status": False,
                "message": "Admin or accounting permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        discount = self.get_object(discount_id)
        if not discount:
            return Response({
                "status": False,
                "message": "Discount not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = DiscountService.delete_discount(discount)
        if success:
            return Response({
                "status": True,
                "message": "Discount deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete discount.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)