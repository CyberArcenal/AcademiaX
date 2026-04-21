import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from canteen.models import OrderItem
from canteen.serializers.order_item import (
    OrderItemMinimalSerializer,
    OrderItemCreateSerializer,
    OrderItemUpdateSerializer,
    OrderItemDisplaySerializer,
)
from canteen.services.order_item import OrderItemService
from canteen.services.order import OrderService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_modify_order(user, order):
    if user.is_staff:
        return True
    if order.user == user:
        return True
    if order.student and order.student.user == user:
        return True
    return False

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class OrderItemCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    product = serializers.IntegerField()
    quantity = serializers.IntegerField()

class OrderItemCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderItemCreateResponseData(allow_null=True)

class OrderItemUpdateResponseData(serializers.Serializer):
    item = OrderItemDisplaySerializer()

class OrderItemUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderItemUpdateResponseData(allow_null=True)

class OrderItemDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class OrderItemDetailResponseData(serializers.Serializer):
    item = OrderItemDisplaySerializer()

class OrderItemDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderItemDetailResponseData(allow_null=True)

class OrderItemListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = OrderItemMinimalSerializer(many=True)

class OrderItemListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderItemListResponseData()

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

class OrderItemListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Order Items"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="order_id", type=int, description="Filter by order ID", required=True),
        ],
        responses={200: OrderItemListResponseSerializer},
        description="List items in an order (requires view permission on order)."
    )
    def get(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id:
            return Response({
                "status": False,
                "message": "order_id parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        order = OrderService.get_order_by_id(order_id)
        if not order:
            return Response({
                "status": False,
                "message": "Order not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_modify_order(request.user, order):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        items = OrderItemService.get_items_by_order(order_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(items, request)
        data = wrap_paginated_data(paginator, page, request, OrderItemMinimalSerializer)
        return Response({
            "status": True,
            "message": "Order items retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Order Items"],
        request=OrderItemCreateSerializer,
        responses={201: OrderItemCreateResponseSerializer, 400: OrderItemCreateResponseSerializer, 403: OrderItemCreateResponseSerializer},
        description="Add an item to an order (user can modify their own pending order)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = OrderItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.validated_data.get('order')
            if not can_modify_order(request.user, order):
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            # Only allow adding to pending orders
            if order.status != 'PD':
                return Response({
                    "status": False,
                    "message": "Cannot add items to a non-pending order.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            item = serializer.save()
            # Recalculate order total
            OrderService.recalculate_total(order)
            return Response({
                "status": True,
                "message": "Item added to order.",
                "data": {
                    "id": item.id,
                    "order": item.order.id,
                    "product": item.product.id,
                    "quantity": item.quantity,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class OrderItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, item_id):
        try:
            return OrderItem.objects.select_related('order', 'product').get(id=item_id)
        except OrderItem.DoesNotExist:
            return None

    @extend_schema(
        tags=["Canteen - Order Items"],
        responses={200: OrderItemDetailResponseSerializer, 404: OrderItemDetailResponseSerializer, 403: OrderItemDetailResponseSerializer},
        description="Retrieve a single order item by ID."
    )
    def get(self, request, item_id):
        item = self.get_object(item_id)
        if not item:
            return Response({
                "status": False,
                "message": "Order item not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_modify_order(request.user, item.order):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = OrderItemDisplaySerializer(item, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Order item retrieved.",
            "data": {"item": data}
        })

    @extend_schema(
        tags=["Canteen - Order Items"],
        request=OrderItemUpdateSerializer,
        responses={200: OrderItemUpdateResponseSerializer, 400: OrderItemUpdateResponseSerializer, 403: OrderItemUpdateResponseSerializer},
        description="Update order item quantity (user can modify their pending order)."
    )
    @transaction.atomic
    def put(self, request, item_id):
        return self._update(request, item_id, partial=False)

    @extend_schema(
        tags=["Canteen - Order Items"],
        request=OrderItemUpdateSerializer,
        responses={200: OrderItemUpdateResponseSerializer, 400: OrderItemUpdateResponseSerializer, 403: OrderItemUpdateResponseSerializer},
        description="Partially update order item."
    )
    @transaction.atomic
    def patch(self, request, item_id):
        return self._update(request, item_id, partial=True)

    def _update(self, request, item_id, partial):
        item = self.get_object(item_id)
        if not item:
            return Response({
                "status": False,
                "message": "Order item not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        order = item.order
        if not can_modify_order(request.user, order):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'PD':
            return Response({
                "status": False,
                "message": "Cannot modify items of a non-pending order.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderItemUpdateSerializer(item, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            # Recalculate order total
            OrderService.recalculate_total(order)
            data = OrderItemDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Order item updated.",
                "data": {"item": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Canteen - Order Items"],
        responses={200: OrderItemDeleteResponseSerializer, 403: OrderItemDeleteResponseSerializer, 404: OrderItemDeleteResponseSerializer},
        description="Remove an item from order."
    )
    @transaction.atomic
    def delete(self, request, item_id):
        item = self.get_object(item_id)
        if not item:
            return Response({
                "status": False,
                "message": "Order item not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        order = item.order
        if not can_modify_order(request.user, order):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'PD':
            return Response({
                "status": False,
                "message": "Cannot remove items from a non-pending order.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        success = OrderItemService.remove_item(item)
        if success:
            OrderService.recalculate_total(order)
            return Response({
                "status": True,
                "message": "Item removed from order.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to remove item.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)