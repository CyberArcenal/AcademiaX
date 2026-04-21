import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from canteen.models import Product
from canteen.serializers.product import (
    ProductMinimalSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    ProductDisplaySerializer,
)
from canteen.services.product import ProductService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_products(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN')

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ProductCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=8, decimal_places=2)

class ProductCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ProductCreateResponseData(allow_null=True)

class ProductUpdateResponseData(serializers.Serializer):
    product = ProductDisplaySerializer()

class ProductUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ProductUpdateResponseData(allow_null=True)

class ProductDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ProductDetailResponseData(serializers.Serializer):
    product = ProductDisplaySerializer()

class ProductDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ProductDetailResponseData(allow_null=True)

class ProductListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ProductMinimalSerializer(many=True)

class ProductListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ProductListResponseData()

class ProductSearchResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ProductMinimalSerializer(many=True)

class ProductSearchResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ProductSearchResponseData()

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

class ProductListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Canteen - Products"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="category_id", type=int, description="Filter by category ID", required=False),
            OpenApiParameter(name="available_only", type=bool, description="Only available products", required=False),
        ],
        responses={200: ProductListResponseSerializer},
        description="List products (public, can filter by category and availability)."
    )
    def get(self, request):
        category_id = request.query_params.get("category_id")
        available_only = request.query_params.get("available_only", "true").lower() == "true"
        if category_id:
            products = ProductService.get_products_by_category(category_id, only_available=available_only)
        else:
            products = Product.objects.all()
            if available_only:
                products = products.filter(is_available=True, stock_quantity__gt=0)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request)
        data = wrap_paginated_data(paginator, page, request, ProductMinimalSerializer)
        return Response({
            "status": True,
            "message": "Products retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Products"],
        request=ProductCreateSerializer,
        responses={201: ProductCreateResponseSerializer, 400: ProductCreateResponseSerializer, 403: ProductCreateResponseSerializer},
        description="Create a new product (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_products(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response({
                "status": True,
                "message": "Product created.",
                "data": {"id": product.id, "name": product.name, "price": product.price}
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, product_id):
        return ProductService.get_product_by_id(product_id)

    @extend_schema(
        tags=["Canteen - Products"],
        responses={200: ProductDetailResponseSerializer, 404: ProductDetailResponseSerializer},
        description="Retrieve a single product by ID."
    )
    def get(self, request, product_id):
        product = self.get_object(product_id)
        if not product:
            return Response({
                "status": False,
                "message": "Product not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = ProductDisplaySerializer(product, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Product retrieved.",
            "data": {"product": data}
        })

    @extend_schema(
        tags=["Canteen - Products"],
        request=ProductUpdateSerializer,
        responses={200: ProductUpdateResponseSerializer, 400: ProductUpdateResponseSerializer, 403: ProductUpdateResponseSerializer},
        description="Update a product (admin only)."
    )
    @transaction.atomic
    def put(self, request, product_id):
        return self._update(request, product_id, partial=False)

    @extend_schema(
        tags=["Canteen - Products"],
        request=ProductUpdateSerializer,
        responses={200: ProductUpdateResponseSerializer, 400: ProductUpdateResponseSerializer, 403: ProductUpdateResponseSerializer},
        description="Partially update a product."
    )
    @transaction.atomic
    def patch(self, request, product_id):
        return self._update(request, product_id, partial=True)

    def _update(self, request, product_id, partial):
        if not can_manage_products(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        product = self.get_object(product_id)
        if not product:
            return Response({
                "status": False,
                "message": "Product not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductUpdateSerializer(product, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ProductDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Product updated.",
                "data": {"product": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Canteen - Products"],
        responses={200: ProductDeleteResponseSerializer, 403: ProductDeleteResponseSerializer, 404: ProductDeleteResponseSerializer},
        description="Delete a product (admin only)."
    )
    @transaction.atomic
    def delete(self, request, product_id):
        if not can_manage_products(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        product = self.get_object(product_id)
        if not product:
            return Response({
                "status": False,
                "message": "Product not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ProductService.delete_product(product)
        if success:
            return Response({
                "status": True,
                "message": "Product deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete product.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductSearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Canteen - Products"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: ProductSearchResponseSerializer},
        description="Search products by name or description."
    )
    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        products = ProductService.search_products(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request)
        data = wrap_paginated_data(paginator, page, request, ProductMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })