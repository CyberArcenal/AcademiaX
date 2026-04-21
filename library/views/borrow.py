import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from library.models import BorrowTransaction
from library.serializers.borrow import (
    BorrowTransactionMinimalSerializer,
    BorrowTransactionCreateSerializer,
    BorrowTransactionUpdateSerializer,
    BorrowTransactionDisplaySerializer,
)
from library.services.borrow import BorrowTransactionService
from library.services.copy import BookCopyService

logger = logging.getLogger(__name__)

def can_view_borrow(user, borrow):
    if user.is_staff:
        return True
    # Students can see their own borrows; teachers/staff may have limited view
    if hasattr(user, 'student_profile'):
        return borrow.borrower == user.student_profile
    return False

def can_manage_borrow(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'LIBRARIAN'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class BorrowCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    copy = serializers.IntegerField()
    borrower = serializers.IntegerField()
    borrow_date = serializers.DateField()
    due_date = serializers.DateField()
    status = serializers.CharField()

class BorrowCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BorrowCreateResponseData(allow_null=True)

class BorrowUpdateResponseData(serializers.Serializer):
    borrow = BorrowTransactionDisplaySerializer()

class BorrowUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BorrowUpdateResponseData(allow_null=True)

class BorrowDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class BorrowDetailResponseData(serializers.Serializer):
    borrow = BorrowTransactionDisplaySerializer()

class BorrowDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BorrowDetailResponseData(allow_null=True)

class BorrowListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = BorrowTransactionMinimalSerializer(many=True)

class BorrowListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BorrowListResponseData()

class BorrowReturnResponseData(serializers.Serializer):
    borrow = BorrowTransactionDisplaySerializer()
    fine = serializers.DictField(required=False)

class BorrowReturnResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = BorrowReturnResponseData()

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

class BorrowTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Library - Borrowing"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="borrower_id", type=int, description="Filter by borrower ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by status", required=False),
        ],
        responses={200: BorrowListResponseSerializer},
        description="List borrow transactions (admins/librarians see all, students see their own)."
    )
    def get(self, request):
        user = request.user
        borrower_id = request.query_params.get("borrower_id")
        status_filter = request.query_params.get("status")

        if user.is_staff or can_manage_borrow(user):
            queryset = BorrowTransaction.objects.all().select_related('copy', 'borrower', 'borrowed_by')
        else:
            if hasattr(user, 'student_profile'):
                queryset = BorrowTransaction.objects.filter(borrower=user.student_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if borrower_id:
            queryset = queryset.filter(borrower_id=borrower_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        queryset = queryset.order_by('-borrow_date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, BorrowTransactionMinimalSerializer)
        return Response({
            "status": True,
            "message": "Borrow transactions retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Library - Borrowing"],
        request=BorrowTransactionCreateSerializer,
        responses={201: BorrowCreateResponseSerializer, 400: BorrowCreateResponseSerializer, 403: BorrowCreateResponseSerializer},
        description="Create a new borrow transaction (librarian/staff only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_borrow(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Set borrowed_by to current user
        data = request.data.copy()
        data['borrowed_by_id'] = request.user.id
        serializer = BorrowTransactionCreateSerializer(data=data)
        if serializer.is_valid():
            borrow = serializer.save()
            return Response({
                "status": True,
                "message": "Borrow transaction created.",
                "data": {
                    "id": borrow.id,
                    "copy": borrow.copy.id,
                    "borrower": borrow.borrower.id,
                    "borrow_date": borrow.borrow_date,
                    "due_date": borrow.due_date,
                    "status": borrow.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BorrowTransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, borrow_id):
        try:
            return BorrowTransaction.objects.select_related('copy', 'borrower', 'borrowed_by').get(id=borrow_id)
        except BorrowTransaction.DoesNotExist:
            return None

    @extend_schema(
        tags=["Library - Borrowing"],
        responses={200: BorrowDetailResponseSerializer, 404: BorrowDetailResponseSerializer, 403: BorrowDetailResponseSerializer},
        description="Retrieve a single borrow transaction by ID."
    )
    def get(self, request, borrow_id):
        borrow = self.get_object(borrow_id)
        if not borrow:
            return Response({
                "status": False,
                "message": "Borrow transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_borrow(request.user, borrow):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = BorrowTransactionDisplaySerializer(borrow, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Borrow transaction retrieved.",
            "data": {"borrow": data}
        })

    @extend_schema(
        tags=["Library - Borrowing"],
        request=BorrowTransactionUpdateSerializer,
        responses={200: BorrowUpdateResponseSerializer, 400: BorrowUpdateResponseSerializer, 403: BorrowUpdateResponseSerializer},
        description="Update a borrow transaction (e.g., due date for renewal)."
    )
    @transaction.atomic
    def put(self, request, borrow_id):
        return self._update(request, borrow_id, partial=False)

    @extend_schema(
        tags=["Library - Borrowing"],
        request=BorrowTransactionUpdateSerializer,
        responses={200: BorrowUpdateResponseSerializer, 400: BorrowUpdateResponseSerializer, 403: BorrowUpdateResponseSerializer},
        description="Partially update a borrow transaction."
    )
    @transaction.atomic
    def patch(self, request, borrow_id):
        return self._update(request, borrow_id, partial=True)

    def _update(self, request, borrow_id, partial):
        if not can_manage_borrow(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        borrow = self.get_object(borrow_id)
        if not borrow:
            return Response({
                "status": False,
                "message": "Borrow transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = BorrowTransactionUpdateSerializer(borrow, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = BorrowTransactionDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Borrow transaction updated.",
                "data": {"borrow": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Library - Borrowing"],
        responses={200: BorrowDeleteResponseSerializer, 403: BorrowDeleteResponseSerializer, 404: BorrowDeleteResponseSerializer},
        description="Delete a borrow transaction (admin only)."
    )
    @transaction.atomic
    def delete(self, request, borrow_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        borrow = self.get_object(borrow_id)
        if not borrow:
            return Response({
                "status": False,
                "message": "Borrow transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = BorrowTransactionService.delete_borrow(borrow)
        if success:
            return Response({
                "status": True,
                "message": "Borrow transaction deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete borrow transaction.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BorrowTransactionReturnView(APIView):
    permission_classes = [IsAuthenticated]

    class ReturnSerializer(serializers.Serializer):
        return_date = serializers.DateField(required=False)
        notes = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["Library - Borrowing"],
        request=ReturnSerializer,
        responses={200: BorrowReturnResponseSerializer, 400: BorrowReturnResponseSerializer, 403: BorrowReturnResponseSerializer},
        description="Return a borrowed book (librarian/staff only)."
    )
    @transaction.atomic
    def post(self, request, borrow_id):
        if not can_manage_borrow(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        borrow = BorrowTransactionService.get_borrow_by_id(borrow_id)
        if not borrow:
            return Response({
                "status": False,
                "message": "Borrow transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if borrow.status in ['RTN', 'CNC']:
            return Response({
                "status": False,
                "message": "Book already returned or cancelled.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.ReturnSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        return_date = serializer.validated_data.get('return_date')
        if not return_date:
            from datetime import date
            return_date = date.today()
        notes = serializer.validated_data.get('notes', '')
        updated = BorrowTransactionService.return_book(borrow, return_date, notes)
        data = BorrowTransactionDisplaySerializer(updated, context={"request": request}).data
        # Check if fine was created
        fine = None
        if hasattr(borrow, 'fine'):
            fine = {
                "id": borrow.fine.id,
                "amount": borrow.fine.amount,
                "days_overdue": borrow.fine.days_overdue,
                "status": borrow.fine.status,
            }
        return Response({
            "status": True,
            "message": "Book returned.",
            "data": {"borrow": data, "fine": fine}
        })


class BorrowTransactionRenewView(APIView):
    permission_classes = [IsAuthenticated]

    class RenewSerializer(serializers.Serializer):
        new_due_date = serializers.DateField()

    @extend_schema(
        tags=["Library - Borrowing"],
        request=RenewSerializer,
        responses={200: BorrowUpdateResponseSerializer, 400: BorrowUpdateResponseSerializer, 403: BorrowUpdateResponseSerializer},
        description="Renew a borrowed book (librarian/staff only)."
    )
    @transaction.atomic
    def post(self, request, borrow_id):
        if not can_manage_borrow(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        borrow = BorrowTransactionService.get_borrow_by_id(borrow_id)
        if not borrow:
            return Response({
                "status": False,
                "message": "Borrow transaction not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if borrow.status != 'BRW':
            return Response({
                "status": False,
                "message": "Only active borrows can be renewed.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.RenewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        new_due_date = serializer.validated_data['new_due_date']
        if new_due_date <= borrow.due_date:
            return Response({
                "status": False,
                "message": "New due date must be after current due date.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = BorrowTransactionService.renew_borrow(borrow, new_due_date)
        data = BorrowTransactionDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Borrow renewed.",
            "data": {"borrow": data}
        })