import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from canteen.models import Order
from canteen.serializers.order import (
    OrderMinimalSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderDisplaySerializer,
)
from django.db import models
from canteen.services.order import OrderService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_view_order(user, order):
    if user.is_staff:
        return True
    if order.student and order.student.user == user:
        return True
    if order.user == user:
        return True
    return False

def can_manage_order(user, order):
    # Staff or the user who created the order (for cancel) or cashier role?
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

class OrderCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    order_number = serializers.CharField()
    status = serializers.CharField()

class OrderCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderCreateResponseData(allow_null=True)

class OrderUpdateResponseData(serializers.Serializer):
    order = OrderDisplaySerializer()

class OrderUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderUpdateResponseData(allow_null=True)

class OrderDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class OrderDetailResponseData(serializers.Serializer):
    order = OrderDisplaySerializer()

class OrderDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderDetailResponseData(allow_null=True)

class OrderListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = OrderMinimalSerializer(many=True)

class OrderListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderListResponseData()

class OrderStatusUpdateResponseData(serializers.Serializer):
    order = OrderDisplaySerializer()

class OrderStatusUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = OrderStatusUpdateResponseData(allow_null=True)

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

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Canteen - Orders"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="status", type=str, description="Filter by order status", required=False),
        ],
        responses={200: OrderListResponseSerializer},
        description="List orders (users see their own, staff see all)."
    )
    def get(self, request):
        user = request.user
        if user.is_staff:
            queryset = Order.objects.all()
        else:
            # For regular users, show orders they made (either via student or user)
            queryset = Order.objects.filter(
                models.Q(user=user) | models.Q(student__user=user)
            )
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, OrderMinimalSerializer)
        return Response({
            "status": True,
            "message": "Orders retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Orders"],
        request=OrderCreateSerializer,
        responses={201: OrderCreateResponseSerializer, 400: OrderCreateResponseSerializer, 403: OrderCreateResponseSerializer},
        description="Create a new order (authenticated users)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            return Response({
                "status": True,
                "message": "Order created.",
                "data": {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, order_id):
        try:
            return Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return None

    @extend_schema(
        tags=["Canteen - Orders"],
        responses={200: OrderDetailResponseSerializer, 404: OrderDetailResponseSerializer, 403: OrderDetailResponseSerializer},
        description="Retrieve a single order by ID."
    )
    def get(self, request, order_id):
        order = self.get_object(order_id)
        if not order:
            return Response({
                "status": False,
                "message": "Order not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_order(request.user, order):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = OrderDisplaySerializer(order, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Order retrieved.",
            "data": {"order": data}
        })

    @extend_schema(
        tags=["Canteen - Orders"],
        request=OrderUpdateSerializer,
        responses={200: OrderUpdateResponseSerializer, 400: OrderUpdateResponseSerializer, 403: OrderUpdateResponseSerializer},
        description="Update an order (e.g., notes)."
    )
    @transaction.atomic
    def put(self, request, order_id):
        return self._update(request, order_id, partial=False)

    @extend_schema(
        tags=["Canteen - Orders"],
        request=OrderUpdateSerializer,
        responses={200: OrderUpdateResponseSerializer, 400: OrderUpdateResponseSerializer, 403: OrderUpdateResponseSerializer},
        description="Partially update an order."
    )
    @transaction.atomic
    def patch(self, request, order_id):
        return self._update(request, order_id, partial=True)

    def _update(self, request, order_id, partial):
        order = self.get_object(order_id)
        if not order:
            return Response({
                "status": False,
                "message": "Order not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_order(request.user, order):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderUpdateSerializer(order, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = OrderDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Order updated.",
                "data": {"order": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Canteen - Orders"],
        responses={200: OrderDeleteResponseSerializer, 403: OrderDeleteResponseSerializer, 404: OrderDeleteResponseSerializer},
        description="Delete an order (cancel)."
    )
    @transaction.atomic
    def delete(self, request, order_id):
        order = self.get_object(order_id)
        if not order:
            return Response({
                "status": False,
                "message": "Order not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_order(request.user, order):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = OrderService.delete_order(order)
        if success:
            return Response({
                "status": True,
                "message": "Order deleted/cancelled.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete order.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    class StatusSerializer(serializers.Serializer):
        status = serializers.CharField()
        reason = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["Canteen - Orders"],
        request=StatusSerializer,
        responses={200: OrderStatusUpdateResponseSerializer, 400: OrderStatusUpdateResponseSerializer, 403: OrderStatusUpdateResponseSerializer},
        description="Update order status (staff only)."
    )
    @transaction.atomic
    def post(self, request, order_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Staff permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        order = OrderService.get_order_by_id(order_id)
        if not order:
            return Response({
                "status": False,
                "message": "Order not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.StatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']
        if new_status == 'CN':
            reason = serializer.validated_data.get('reason', '')
            updated = OrderService.cancel_order(order, reason)
        else:
            updated = OrderService.update_order_status(order, new_status, request.user)
        data = OrderDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Order status updated.",
            "data": {"order": data}
        })