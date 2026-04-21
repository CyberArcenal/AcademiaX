import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from canteen.models import Category
from canteen.serializers.category import (
    CategoryMinimalSerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    CategoryDisplaySerializer,
)
from canteen.services.category import CategoryService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_categories(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN')

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class CategoryCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class CategoryCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CategoryCreateResponseData(allow_null=True)

class CategoryUpdateResponseData(serializers.Serializer):
    category = CategoryDisplaySerializer()

class CategoryUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CategoryUpdateResponseData(allow_null=True)

class CategoryDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class CategoryDetailResponseData(serializers.Serializer):
    category = CategoryDisplaySerializer()

class CategoryDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CategoryDetailResponseData(allow_null=True)

class CategoryListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = CategoryMinimalSerializer(many=True)

class CategoryListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CategoryListResponseData()

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

class CategoryListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Canteen - Categories"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: CategoryListResponseSerializer},
        description="List product categories (public)."
    )
    def get(self, request):
        categories = CategoryService.get_all_categories()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(categories, request)
        data = wrap_paginated_data(paginator, page, request, CategoryMinimalSerializer)
        return Response({
            "status": True,
            "message": "Categories retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Canteen - Categories"],
        request=CategoryCreateSerializer,
        responses={201: CategoryCreateResponseSerializer, 400: CategoryCreateResponseSerializer, 403: CategoryCreateResponseSerializer},
        description="Create a new category (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_categories(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = CategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response({
                "status": True,
                "message": "Category created.",
                "data": {"id": category.id, "name": category.get_name_display()}
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, category_id):
        return CategoryService.get_category_by_id(category_id)

    @extend_schema(
        tags=["Canteen - Categories"],
        responses={200: CategoryDetailResponseSerializer, 404: CategoryDetailResponseSerializer},
        description="Retrieve a single category by ID."
    )
    def get(self, request, category_id):
        category = self.get_object(category_id)
        if not category:
            return Response({
                "status": False,
                "message": "Category not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = CategoryDisplaySerializer(category, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Category retrieved.",
            "data": {"category": data}
        })

    @extend_schema(
        tags=["Canteen - Categories"],
        request=CategoryUpdateSerializer,
        responses={200: CategoryUpdateResponseSerializer, 400: CategoryUpdateResponseSerializer, 403: CategoryUpdateResponseSerializer},
        description="Update a category (admin only)."
    )
    @transaction.atomic
    def put(self, request, category_id):
        return self._update(request, category_id, partial=False)

    @extend_schema(
        tags=["Canteen - Categories"],
        request=CategoryUpdateSerializer,
        responses={200: CategoryUpdateResponseSerializer, 400: CategoryUpdateResponseSerializer, 403: CategoryUpdateResponseSerializer},
        description="Partially update a category."
    )
    @transaction.atomic
    def patch(self, request, category_id):
        return self._update(request, category_id, partial=True)

    def _update(self, request, category_id, partial):
        if not can_manage_categories(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        category = self.get_object(category_id)
        if not category:
            return Response({
                "status": False,
                "message": "Category not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = CategoryUpdateSerializer(category, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = CategoryDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Category updated.",
                "data": {"category": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Canteen - Categories"],
        responses={200: CategoryDeleteResponseSerializer, 403: CategoryDeleteResponseSerializer, 404: CategoryDeleteResponseSerializer},
        description="Delete a category (admin only)."
    )
    @transaction.atomic
    def delete(self, request, category_id):
        if not can_manage_categories(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        category = self.get_object(category_id)
        if not category:
            return Response({
                "status": False,
                "message": "Category not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = CategoryService.delete_category(category)
        if success:
            return Response({
                "status": True,
                "message": "Category deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete category.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)