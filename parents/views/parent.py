import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from parents.models import Parent
from parents.serializers.parent import (
    ParentMinimalSerializer,
    ParentCreateSerializer,
    ParentUpdateSerializer,
    ParentDisplaySerializer,
)
from parents.services.parent import ParentService

logger = logging.getLogger(__name__)

def can_view_parent(user, parent):
    if user.is_staff:
        return True
    # Parents can view their own record; students might view their parents? Optional.
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return parent == user.parent_profile
    return False

def can_manage_parent(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ParentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.IntegerField()
    contact_number = serializers.CharField()

class ParentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentCreateResponseData(allow_null=True)

class ParentUpdateResponseData(serializers.Serializer):
    parent = ParentDisplaySerializer()

class ParentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentUpdateResponseData(allow_null=True)

class ParentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ParentDetailResponseData(serializers.Serializer):
    parent = ParentDisplaySerializer()

class ParentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentDetailResponseData(allow_null=True)

class ParentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ParentMinimalSerializer(many=True)

class ParentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ParentListResponseData()

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

class ParentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Parents"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: ParentListResponseSerializer},
        description="List parents (admin/registrar only)."
    )
    def get(self, request):
        if not can_manage_parent(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        parents = ParentService.get_all_parents(active_only=active_only)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(parents, request)
        data = wrap_paginated_data(paginator, page, request, ParentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Parents retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Parents"],
        request=ParentCreateSerializer,
        responses={201: ParentCreateResponseSerializer, 400: ParentCreateResponseSerializer, 403: ParentCreateResponseSerializer},
        description="Create a parent record (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_parent(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = ParentCreateSerializer(data=request.data)
        if serializer.is_valid():
            parent = serializer.save()
            return Response({
                "status": True,
                "message": "Parent record created.",
                "data": {
                    "id": parent.id,
                    "user": parent.user.id,
                    "contact_number": parent.contact_number,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ParentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, parent_id):
        try:
            return Parent.objects.select_related('user').get(id=parent_id)
        except Parent.DoesNotExist:
            return None

    @extend_schema(
        tags=["Parents"],
        responses={200: ParentDetailResponseSerializer, 404: ParentDetailResponseSerializer, 403: ParentDetailResponseSerializer},
        description="Retrieve a single parent by ID."
    )
    def get(self, request, parent_id):
        parent = self.get_object(parent_id)
        if not parent:
            return Response({
                "status": False,
                "message": "Parent record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_parent(request.user, parent):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ParentDisplaySerializer(parent, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Parent retrieved.",
            "data": {"parent": data}
        })

    @extend_schema(
        tags=["Parents"],
        request=ParentUpdateSerializer,
        responses={200: ParentUpdateResponseSerializer, 400: ParentUpdateResponseSerializer, 403: ParentUpdateResponseSerializer},
        description="Update a parent record (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, parent_id):
        return self._update(request, parent_id, partial=False)

    @extend_schema(
        tags=["Parents"],
        request=ParentUpdateSerializer,
        responses={200: ParentUpdateResponseSerializer, 400: ParentUpdateResponseSerializer, 403: ParentUpdateResponseSerializer},
        description="Partially update a parent record."
    )
    @transaction.atomic
    def patch(self, request, parent_id):
        return self._update(request, parent_id, partial=True)

    def _update(self, request, parent_id, partial):
        if not can_manage_parent(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        parent = self.get_object(parent_id)
        if not parent:
            return Response({
                "status": False,
                "message": "Parent record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ParentUpdateSerializer(parent, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ParentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Parent updated.",
                "data": {"parent": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Parents"],
        responses={200: ParentDeleteResponseSerializer, 403: ParentDeleteResponseSerializer, 404: ParentDeleteResponseSerializer},
        description="Delete a parent record (admin only)."
    )
    @transaction.atomic
    def delete(self, request, parent_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        parent = self.get_object(parent_id)
        if not parent:
            return Response({
                "status": False,
                "message": "Parent record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ParentService.delete_parent(parent)
        if success:
            return Response({
                "status": True,
                "message": "Parent record deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete parent record.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Parents"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: ParentListResponseSerializer},
        description="Search parents by name or contact (admin/registrar only)."
    )
    def get(self, request):
        if not can_manage_parent(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        parents = ParentService.search_parents(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(parents, request)
        data = wrap_paginated_data(paginator, page, request, ParentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })