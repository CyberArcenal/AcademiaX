import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from library.models import Book
from library.serializers.book import (
    BookMinimalSerializer,
    BookCreateSerializer,
    BookUpdateSerializer,
    BookDisplaySerializer,
)
from library.services.book import BookService

logger = logging.getLogger(__name__)

def can_manage_book(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class BookCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    isbn = serializers.CharField()

class BookCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BookCreateResponseData(allow_null=True)

class BookUpdateResponseData(serializers.Serializer):
    book = BookDisplaySerializer()

class BookUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BookUpdateResponseData(allow_null=True)

class BookDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class BookDetailResponseData(serializers.Serializer):
    book = BookDisplaySerializer()

class BookDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BookDetailResponseData(allow_null=True)

class BookListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = BookMinimalSerializer(many=True)

class BookListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BookListResponseData()

class BookSearchResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = BookMinimalSerializer(many=True)

class BookSearchResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BookSearchResponseData()

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

class BookListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Library - Books"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="publisher_id", type=int, description="Filter by publisher ID", required=False),
            OpenApiParameter(name="author_id", type=int, description="Filter by author ID", required=False),
        ],
        responses={200: BookListResponseSerializer},
        description="List books (public)."
    )
    def get(self, request):
        publisher_id = request.query_params.get("publisher_id")
        author_id = request.query_params.get("author_id")
        if publisher_id:
            books = Book.objects.filter(publisher_id=publisher_id)
        elif author_id:
            books = BookService.get_books_by_author(author_id)
        else:
            books = BookService.get_all_books()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(books, request)
        data = wrap_paginated_data(paginator, page, request, BookMinimalSerializer)
        return Response({
            "status": True,
            "message": "Books retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Library - Books"],
        request=BookCreateSerializer,
        responses={201: BookCreateResponseSerializer, 400: BookCreateResponseSerializer, 403: BookCreateResponseSerializer},
        description="Create a new book (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_book(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = BookCreateSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save()
            return Response({
                "status": True,
                "message": "Book created.",
                "data": {
                    "id": book.id,
                    "title": book.title,
                    "isbn": book.isbn,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BookDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, book_id):
        return BookService.get_book_by_id(book_id)

    @extend_schema(
        tags=["Library - Books"],
        responses={200: BookDetailResponseSerializer, 404: BookDetailResponseSerializer},
        description="Retrieve a single book by ID."
    )
    def get(self, request, book_id):
        book = self.get_object(book_id)
        if not book:
            return Response({
                "status": False,
                "message": "Book not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = BookDisplaySerializer(book, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Book retrieved.",
            "data": {"book": data}
        })

    @extend_schema(
        tags=["Library - Books"],
        request=BookUpdateSerializer,
        responses={200: BookUpdateResponseSerializer, 400: BookUpdateResponseSerializer, 403: BookUpdateResponseSerializer},
        description="Update a book (admin only)."
    )
    @transaction.atomic
    def put(self, request, book_id):
        return self._update(request, book_id, partial=False)

    @extend_schema(
        tags=["Library - Books"],
        request=BookUpdateSerializer,
        responses={200: BookUpdateResponseSerializer, 400: BookUpdateResponseSerializer, 403: BookUpdateResponseSerializer},
        description="Partially update a book."
    )
    @transaction.atomic
    def patch(self, request, book_id):
        return self._update(request, book_id, partial=True)

    def _update(self, request, book_id, partial):
        if not can_manage_book(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        book = self.get_object(book_id)
        if not book:
            return Response({
                "status": False,
                "message": "Book not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = BookUpdateSerializer(book, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = BookDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Book updated.",
                "data": {"book": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Library - Books"],
        responses={200: BookDeleteResponseSerializer, 403: BookDeleteResponseSerializer, 404: BookDeleteResponseSerializer},
        description="Delete a book (admin only)."
    )
    @transaction.atomic
    def delete(self, request, book_id):
        if not can_manage_book(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        book = self.get_object(book_id)
        if not book:
            return Response({
                "status": False,
                "message": "Book not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = BookService.delete_book(book)
        if success:
            return Response({
                "status": True,
                "message": "Book deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete book.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookSearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Library - Books"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: BookSearchResponseSerializer},
        description="Search books by title, ISBN, subject, or author."
    )
    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        books = BookService.search_books(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(books, request)
        data = wrap_paginated_data(paginator, page, request, BookMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })