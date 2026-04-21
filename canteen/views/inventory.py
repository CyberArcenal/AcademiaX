import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from canteen.models import InventoryLog, Product
from canteen.serializers.inventory import (
    InventoryLogMinimalSerializer,
    InventoryLogCreateSerializer,
    InventoryLogUpdateSerializer,
    InventoryLogDisplaySerializer,
)
from canteen.services.inventory import InventoryLogService
from canteen.services.product import ProductService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_inventory(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN')

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class InventoryLogCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    product = serializers.IntegerField()
    quantity_change = serializers.IntegerField()
    new_quantity = serializers.IntegerField()

class InventoryLogCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = InventoryLogCreateResponseData(allow_null=True)

class InventoryLogUpdateResponseData(serializers.Serializer):
    log = InventoryLogDisplaySerializer()

class InventoryLogUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = InventoryLogUpdateResponseData(allow_null=True)

class InventoryLogDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class InventoryLogDetailResponseData(serializers.Serializer):
    log = InventoryLogDisplaySerializer()

class InventoryLogDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = InventoryLogDetailResponseData(allow_null=True)

class InventoryLogListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = InventoryLogMinimalSerializer(many=True)

class InventoryLogListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = InventoryLogListResponseData()

class LowStockResponseData(serializers.Serializer):
    product_id = serializers.IntegerField()
    name = serializers.CharField()
    stock_quantity = serializers.IntegerField()
    threshold = serializers.IntegerField()

class LowStockResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.ListField(child=LowStockResponseData())

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

class InventoryLogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Inventory"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="product_id", type=int, description="Filter by product ID", required=False),
        ],
        responses={200: InventoryLogListResponseSerializer},
        description="List inventory logs (admin only)."
    )
    def get(self, request):
        if not can_manage_inventory(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        product_id = request.query_params.get("product_id")
        if product_id:
            logs = InventoryLogService.get_logs_by_product(product_id)
        else:
            logs = InventoryLog.objects.all().select_related('product', 'recorded_by').order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(logs, request)
        data = wrap_paginated_data(paginator, page, request, InventoryLogMinimalSerializer)
        return Response({
            "status": True,
            "message": "Inventory logs retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Inventory"],
        request=InventoryLogCreateSerializer,
        responses={201: InventoryLogCreateResponseSerializer, 400: InventoryLogCreateResponseSerializer, 403: InventoryLogCreateResponseSerializer},
        description="Create an inventory log (stock in/out)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_inventory(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Include recorded_by from request user
        data = request.data.copy()
        data['recorded_by_id'] = request.user.id
        serializer = InventoryLogCreateSerializer(data=data)
        if serializer.is_valid():
            log = serializer.save()
            return Response({
                "status": True,
                "message": "Inventory log created.",
                "data": {
                    "id": log.id,
                    "product": log.product.id,
                    "quantity_change": log.quantity_change,
                    "new_quantity": log.new_quantity,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class InventoryLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, log_id):
        try:
            return InventoryLog.objects.select_related('product', 'recorded_by').get(id=log_id)
        except InventoryLog.DoesNotExist:
            return None

    @extend_schema(
        tags=["Canteen - Inventory"],
        responses={200: InventoryLogDetailResponseSerializer, 404: InventoryLogDetailResponseSerializer, 403: InventoryLogDetailResponseSerializer},
        description="Retrieve a single inventory log by ID."
    )
    def get(self, request, log_id):
        if not can_manage_inventory(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Inventory log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = InventoryLogDisplaySerializer(log, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Inventory log retrieved.",
            "data": {"log": data}
        })

    @extend_schema(
        tags=["Canteen - Inventory"],
        request=InventoryLogUpdateSerializer,
        responses={200: InventoryLogUpdateResponseSerializer, 400: InventoryLogUpdateResponseSerializer, 403: InventoryLogUpdateResponseSerializer},
        description="Update an inventory log (e.g., notes)."
    )
    @transaction.atomic
    def put(self, request, log_id):
        return self._update(request, log_id, partial=False)

    @extend_schema(
        tags=["Canteen - Inventory"],
        request=InventoryLogUpdateSerializer,
        responses={200: InventoryLogUpdateResponseSerializer, 400: InventoryLogUpdateResponseSerializer, 403: InventoryLogUpdateResponseSerializer},
        description="Partially update an inventory log."
    )
    @transaction.atomic
    def patch(self, request, log_id):
        return self._update(request, log_id, partial=True)

    def _update(self, request, log_id, partial):
        if not can_manage_inventory(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Inventory log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = InventoryLogUpdateSerializer(log, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = InventoryLogDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Inventory log updated.",
                "data": {"log": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Canteen - Inventory"],
        responses={200: InventoryLogDeleteResponseSerializer, 403: InventoryLogDeleteResponseSerializer, 404: InventoryLogDeleteResponseSerializer},
        description="Delete an inventory log (admin only)."
    )
    @transaction.atomic
    def delete(self, request, log_id):
        if not can_manage_inventory(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        log = self.get_object(log_id)
        if not log:
            return Response({
                "status": False,
                "message": "Inventory log not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = InventoryLogService.delete_log(log)
        if success:
            return Response({
                "status": True,
                "message": "Inventory log deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete inventory log.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LowStockAlertView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Inventory"],
        parameters=[
            OpenApiParameter(name="threshold", type=int, description="Stock threshold (default 10)", required=False),
        ],
        responses={200: LowStockResponseSerializer, 403: LowStockResponseSerializer},
        description="Get products with stock below threshold (admin only)."
    )
    def get(self, request):
        if not can_manage_inventory(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        threshold = int(request.query_params.get("threshold", 10))
        products = InventoryLogService.get_low_stock_products(threshold)
        data = [
            {
                "product_id": p.id,
                "name": p.name,
                "stock_quantity": p.stock_quantity,
                "threshold": threshold,
            }
            for p in products
        ]
        return Response({
            "status": True,
            "message": f"Products with stock below {threshold}.",
            "data": data
        })