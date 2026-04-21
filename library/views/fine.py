import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from library.models import Fine
from library.serializers.fine import (
    FineMinimalSerializer,
    FineCreateSerializer,
    FineUpdateSerializer,
    FineDisplaySerializer,
)
from library.services.fine import FineService
from library.services.borrow import BorrowTransactionService

logger = logging.getLogger(__name__)

def can_view_fine(user, fine):
    if user.is_staff:
        return True
    # Students can see fines on their borrows
    if hasattr(user, 'student_profile'):
        return fine.borrow_transaction.borrower == user.student_profile
    return False

def can_manage_fine(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'LIBRARIAN'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class FineCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    borrow_transaction = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)

class FineCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FineCreateResponseData(allow_null=True)

class FineUpdateResponseData(serializers.Serializer):
    fine = FineDisplaySerializer()

class FineUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FineUpdateResponseData(allow_null=True)

class FineDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class FineDetailResponseData(serializers.Serializer):
    fine = FineDisplaySerializer()

class FineDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FineDetailResponseData(allow_null=True)

class FineListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = FineMinimalSerializer(many=True)

class FineListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FineListResponseData()

class FinePayResponseData(serializers.Serializer):
    fine = FineDisplaySerializer()
    receipt_number = serializers.CharField()

class FinePayResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = FinePayResponseData()

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

class FineListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Library - Fines"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="borrower_id", type=int, description="Filter by borrower ID (student)", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by fine status", required=False),
        ],
        responses={200: FineListResponseSerializer},
        description="List fines (admins/librarians see all, students see their own)."
    )
    def get(self, request):
        user = request.user
        borrower_id = request.query_params.get("borrower_id")
        status_filter = request.query_params.get("status")

        if user.is_staff or can_manage_fine(user):
            queryset = Fine.objects.all().select_related('borrow_transaction', 'paid_by')
        else:
            if hasattr(user, 'student_profile'):
                queryset = Fine.objects.filter(borrow_transaction__borrower=user.student_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if borrower_id:
            queryset = queryset.filter(borrow_transaction__borrower_id=borrower_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, FineMinimalSerializer)
        return Response({
            "status": True,
            "message": "Fines retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Library - Fines"],
        request=FineCreateSerializer,
        responses={201: FineCreateResponseSerializer, 400: FineCreateResponseSerializer, 403: FineCreateResponseSerializer},
        description="Create a fine (usually auto-generated on overdue, but manual override possible)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_fine(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = FineCreateSerializer(data=request.data)
        if serializer.is_valid():
            fine = serializer.save()
            return Response({
                "status": True,
                "message": "Fine created.",
                "data": {
                    "id": fine.id,
                    "borrow_transaction": fine.borrow_transaction.id,
                    "amount": fine.amount,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FineDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, fine_id):
        try:
            return Fine.objects.select_related('borrow_transaction', 'paid_by').get(id=fine_id)
        except Fine.DoesNotExist:
            return None

    @extend_schema(
        tags=["Library - Fines"],
        responses={200: FineDetailResponseSerializer, 404: FineDetailResponseSerializer, 403: FineDetailResponseSerializer},
        description="Retrieve a single fine by ID."
    )
    def get(self, request, fine_id):
        fine = self.get_object(fine_id)
        if not fine:
            return Response({
                "status": False,
                "message": "Fine not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_fine(request.user, fine):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = FineDisplaySerializer(fine, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Fine retrieved.",
            "data": {"fine": data}
        })

    @extend_schema(
        tags=["Library - Fines"],
        request=FineUpdateSerializer,
        responses={200: FineUpdateResponseSerializer, 400: FineUpdateResponseSerializer, 403: FineUpdateResponseSerializer},
        description="Update a fine (e.g., waive, adjust amount)."
    )
    @transaction.atomic
    def put(self, request, fine_id):
        return self._update(request, fine_id, partial=False)

    @extend_schema(
        tags=["Library - Fines"],
        request=FineUpdateSerializer,
        responses={200: FineUpdateResponseSerializer, 400: FineUpdateResponseSerializer, 403: FineUpdateResponseSerializer},
        description="Partially update a fine."
    )
    @transaction.atomic
    def patch(self, request, fine_id):
        return self._update(request, fine_id, partial=True)

    def _update(self, request, fine_id, partial):
        if not can_manage_fine(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        fine = self.get_object(fine_id)
        if not fine:
            return Response({
                "status": False,
                "message": "Fine not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = FineUpdateSerializer(fine, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = FineDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Fine updated.",
                "data": {"fine": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Library - Fines"],
        responses={200: FineDeleteResponseSerializer, 403: FineDeleteResponseSerializer, 404: FineDeleteResponseSerializer},
        description="Delete a fine (admin only)."
    )
    @transaction.atomic
    def delete(self, request, fine_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        fine = self.get_object(fine_id)
        if not fine:
            return Response({
                "status": False,
                "message": "Fine not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = FineService.delete_fine(fine)
        if success:
            return Response({
                "status": True,
                "message": "Fine deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete fine.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinePayView(APIView):
    permission_classes = [IsAuthenticated]

    class PaySerializer(serializers.Serializer):
        receipt_number = serializers.CharField(required=False, allow_blank=True)
        remarks = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["Library - Fines"],
        request=PaySerializer,
        responses={200: FinePayResponseSerializer, 400: FinePayResponseSerializer, 403: FinePayResponseSerializer},
        description="Pay a fine (librarian/admin only)."
    )
    @transaction.atomic
    def post(self, request, fine_id):
        if not can_manage_fine(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        fine = FineService.get_fine_by_id(fine_id)
        if not fine:
            return Response({
                "status": False,
                "message": "Fine not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if fine.status == 'PD':
            return Response({
                "status": False,
                "message": "Fine already paid.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.PaySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = FineService.pay_fine(
            fine,
            paid_by=request.user,
            receipt_number=serializer.validated_data.get('receipt_number', ''),
            remarks=serializer.validated_data.get('remarks', '')
        )
        data = FineDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Fine paid.",
            "data": {"fine": data, "receipt_number": updated.receipt_number}
        })


class FineWaiveView(APIView):
    permission_classes = [IsAuthenticated]

    class WaiveSerializer(serializers.Serializer):
        remarks = serializers.CharField(required=False, allow_blank=True)

    @extend_schema(
        tags=["Library - Fines"],
        request=WaiveSerializer,
        responses={200: FineUpdateResponseSerializer, 400: FineUpdateResponseSerializer, 403: FineUpdateResponseSerializer},
        description="Waive a fine (admin only)."
    )
    @transaction.atomic
    def post(self, request, fine_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        fine = FineService.get_fine_by_id(fine_id)
        if not fine:
            return Response({
                "status": False,
                "message": "Fine not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if fine.status != 'PND':
            return Response({
                "status": False,
                "message": "Only pending fines can be waived.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.WaiveSerializer(data=request.data)
        remarks = serializer.validated_data.get('remarks', '') if serializer.is_valid() else ''
        updated = FineService.waive_fine(fine, remarks)
        data = FineDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Fine waived.",
            "data": {"fine": data}
        })