import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from library.models import BookCopy
from library.serializers.copy import (
    BookCopyMinimalSerializer,
    BookCopyCreateSerializer,
    BookCopyUpdateSerializer,
    BookCopyDisplaySerializer,
)
from library.services.copy import BookCopyService

logger = logging.getLogger(__name__)

def can_manage_copy(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class CopyCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    book = serializers.IntegerField()
    copy_number = serializers.CharField()
    barcode = serializers.CharField()

class CopyCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CopyCreateResponseData(allow_null=True)

class CopyUpdateResponseData(serializers.Serializer):
    copy = BookCopyDisplaySerializer()

class CopyUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CopyUpdateResponseData(allow_null=True)

class CopyDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class CopyDetailResponseData(serializers.Serializer):
    copy = BookCopyDisplaySerializer()

class CopyDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CopyDetailResponseData(allow_null=True)

class CopyListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = BookCopyMinimalSerializer(many=True)

class CopyListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = CopyListResponseData()

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

class BookCopyListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Library - Copies"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="book_id", type=int, description="Filter by book ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by copy status", required=False),
        ],
        responses={200: CopyListResponseSerializer},
        description="List book copies (public)."
    )
    def get(self, request):
        book_id = request.query_params.get("book_id")
        status_filter = request.query_params.get("status")
        if book_id:
            copies = BookCopyService.get_copies_by_book(book_id)
        elif status_filter:
            copies = BookCopyService.get_copies_by_status(status_filter)
        else:
            copies = BookCopy.objects.all().select_related('book')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(copies, request)
        data = wrap_paginated_data(paginator, page, request, BookCopyMinimalSerializer)
        return Response({
            "status": True,
            "message": "Book copies retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Library - Copies"],
        request=BookCopyCreateSerializer,
        responses={201: CopyCreateResponseSerializer, 400: CopyCreateResponseSerializer, 403: CopyCreateResponseSerializer},
        description="Create a new book copy (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_copy(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = BookCopyCreateSerializer(data=request.data)
        if serializer.is_valid():
            copy = serializer.save()
            return Response({
                "status": True,
                "message": "Book copy created.",
                "data": {
                    "id": copy.id,
                    "book": copy.book.id,
                    "copy_number": copy.copy_number,
                    "barcode": copy.barcode,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BookCopyDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, copy_id):
        try:
            return BookCopy.objects.select_related('book').get(id=copy_id)
        except BookCopy.DoesNotExist:
            return None

    @extend_schema(
        tags=["Library - Copies"],
        responses={200: CopyDetailResponseSerializer, 404: CopyDetailResponseSerializer},
        description="Retrieve a single book copy by ID."
    )
    def get(self, request, copy_id):
        copy = self.get_object(copy_id)
        if not copy:
            return Response({
                "status": False,
                "message": "Book copy not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = BookCopyDisplaySerializer(copy, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Book copy retrieved.",
            "data": {"copy": data}
        })

    @extend_schema(
        tags=["Library - Copies"],
        request=BookCopyUpdateSerializer,
        responses={200: CopyUpdateResponseSerializer, 400: CopyUpdateResponseSerializer, 403: CopyUpdateResponseSerializer},
        description="Update a book copy (admin only)."
    )
    @transaction.atomic
    def put(self, request, copy_id):
        return self._update(request, copy_id, partial=False)

    @extend_schema(
        tags=["Library - Copies"],
        request=BookCopyUpdateSerializer,
        responses={200: CopyUpdateResponseSerializer, 400: CopyUpdateResponseSerializer, 403: CopyUpdateResponseSerializer},
        description="Partially update a book copy."
    )
    @transaction.atomic
    def patch(self, request, copy_id):
        return self._update(request, copy_id, partial=True)

    def _update(self, request, copy_id, partial):
        if not can_manage_copy(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        copy = self.get_object(copy_id)
        if not copy:
            return Response({
                "status": False,
                "message": "Book copy not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = BookCopyUpdateSerializer(copy, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = BookCopyDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Book copy updated.",
                "data": {"copy": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Library - Copies"],
        responses={200: CopyDeleteResponseSerializer, 403: CopyDeleteResponseSerializer, 404: CopyDeleteResponseSerializer},
        description="Delete a book copy (admin only)."
    )
    @transaction.atomic
    def delete(self, request, copy_id):
        if not can_manage_copy(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        copy = self.get_object(copy_id)
        if not copy:
            return Response({
                "status": False,
                "message": "Book copy not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = BookCopyService.delete_copy(copy)
        if success:
            return Response({
                "status": True,
                "message": "Book copy deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete book copy.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookCopyUpdateStatusView(APIView):
    permission_classes = [IsAuthenticated]

    class StatusSerializer(serializers.Serializer):
        status = serializers.CharField()

    @extend_schema(
        tags=["Library - Copies"],
        request=StatusSerializer,
        responses={200: CopyUpdateResponseSerializer, 400: CopyUpdateResponseSerializer, 403: CopyUpdateResponseSerializer},
        description="Update book copy status (admin only)."
    )
    @transaction.atomic
    def post(self, request, copy_id):
        if not can_manage_copy(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        copy = BookCopyService.get_copy_by_id(copy_id)
        if not copy:
            return Response({
                "status": False,
                "message": "Book copy not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.StatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = BookCopyService.update_status(copy, serializer.validated_data['status'])
        data = BookCopyDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Copy status updated.",
            "data": {"copy": data}
        })