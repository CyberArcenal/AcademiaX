import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from library.models import Author
from library.serializers.author import (
    AuthorMinimalSerializer,
    AuthorCreateSerializer,
    AuthorUpdateSerializer,
    AuthorDisplaySerializer,
)
from library.services.author import AuthorService

logger = logging.getLogger(__name__)

def can_manage_author(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AuthorCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()

class AuthorCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AuthorCreateResponseData(allow_null=True)

class AuthorUpdateResponseData(serializers.Serializer):
    author = AuthorDisplaySerializer()

class AuthorUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AuthorUpdateResponseData(allow_null=True)

class AuthorDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AuthorDetailResponseData(serializers.Serializer):
    author = AuthorDisplaySerializer()

class AuthorDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AuthorDetailResponseData(allow_null=True)

class AuthorListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AuthorMinimalSerializer(many=True)

class AuthorListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AuthorListResponseData()

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

class AuthorListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Library - Authors"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: AuthorListResponseSerializer},
        description="List authors (public)."
    )
    def get(self, request):
        authors = AuthorService.get_all_authors()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(authors, request)
        data = wrap_paginated_data(paginator, page, request, AuthorMinimalSerializer)
        return Response({
            "status": True,
            "message": "Authors retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Library - Authors"],
        request=AuthorCreateSerializer,
        responses={201: AuthorCreateResponseSerializer, 400: AuthorCreateResponseSerializer, 403: AuthorCreateResponseSerializer},
        description="Create a new author (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_author(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = AuthorCreateSerializer(data=request.data)
        if serializer.is_valid():
            author = serializer.save()
            return Response({
                "status": True,
                "message": "Author created.",
                "data": {
                    "id": author.id,
                    "first_name": author.first_name,
                    "last_name": author.last_name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AuthorDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, author_id):
        return AuthorService.get_author_by_id(author_id)

    @extend_schema(
        tags=["Library - Authors"],
        responses={200: AuthorDetailResponseSerializer, 404: AuthorDetailResponseSerializer},
        description="Retrieve a single author by ID."
    )
    def get(self, request, author_id):
        author = self.get_object(author_id)
        if not author:
            return Response({
                "status": False,
                "message": "Author not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = AuthorDisplaySerializer(author, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Author retrieved.",
            "data": {"author": data}
        })

    @extend_schema(
        tags=["Library - Authors"],
        request=AuthorUpdateSerializer,
        responses={200: AuthorUpdateResponseSerializer, 400: AuthorUpdateResponseSerializer, 403: AuthorUpdateResponseSerializer},
        description="Update an author (admin only)."
    )
    @transaction.atomic
    def put(self, request, author_id):
        return self._update(request, author_id, partial=False)

    @extend_schema(
        tags=["Library - Authors"],
        request=AuthorUpdateSerializer,
        responses={200: AuthorUpdateResponseSerializer, 400: AuthorUpdateResponseSerializer, 403: AuthorUpdateResponseSerializer},
        description="Partially update an author."
    )
    @transaction.atomic
    def patch(self, request, author_id):
        return self._update(request, author_id, partial=True)

    def _update(self, request, author_id, partial):
        if not can_manage_author(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        author = self.get_object(author_id)
        if not author:
            return Response({
                "status": False,
                "message": "Author not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = AuthorUpdateSerializer(author, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = AuthorDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Author updated.",
                "data": {"author": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Library - Authors"],
        responses={200: AuthorDeleteResponseSerializer, 403: AuthorDeleteResponseSerializer, 404: AuthorDeleteResponseSerializer},
        description="Delete an author (admin only)."
    )
    @transaction.atomic
    def delete(self, request, author_id):
        if not can_manage_author(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        author = self.get_object(author_id)
        if not author:
            return Response({
                "status": False,
                "message": "Author not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = AuthorService.delete_author(author)
        if success:
            return Response({
                "status": True,
                "message": "Author deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete author.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)