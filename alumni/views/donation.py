import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from alumni.models import Donation
from alumni.serializers.donation import (
    DonationMinimalSerializer,
    DonationCreateSerializer,
    DonationUpdateSerializer,
    DonationDisplaySerializer,
)
from alumni.services.donation import DonationService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class DonationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    alumni = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

class DonationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DonationCreateResponseData(allow_null=True)

class DonationUpdateResponseData(serializers.Serializer):
    donation = DonationDisplaySerializer()

class DonationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DonationUpdateResponseData(allow_null=True)

class DonationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class DonationDetailResponseData(serializers.Serializer):
    donation = DonationDisplaySerializer()

class DonationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DonationDetailResponseData(allow_null=True)

class DonationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = DonationMinimalSerializer(many=True)

class DonationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DonationListResponseData()

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

class DonationListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni - Donations"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="alumni_id", type=int, description="Filter by alumni ID", required=False),
            OpenApiParameter(name="purpose", type=str, description="Filter by purpose", required=False),
        ],
        responses={200: DonationListResponseSerializer},
        description="List donation records, optionally filtered by alumni or purpose."
    )
    def get(self, request):
        alumni_id = request.query_params.get("alumni_id")
        purpose = request.query_params.get("purpose")
        if alumni_id:
            donations = DonationService.get_donations_by_alumni(alumni_id)
        elif purpose:
            donations = DonationService.get_donations_by_purpose(purpose)
        else:
            donations = Donation.objects.all().select_related('alumni').order_by('-date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(donations, request)
        data = wrap_paginated_data(paginator, page, request, DonationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Donation records retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Alumni - Donations"],
        request=DonationCreateSerializer,
        responses={201: DonationCreateResponseSerializer, 400: DonationCreateResponseSerializer},
        description="Create a new donation record."
    )
    @transaction.atomic
    def post(self, request):
        serializer = DonationCreateSerializer(data=request.data)
        if serializer.is_valid():
            donation = serializer.save()
            return Response({
                "status": True,
                "message": "Donation record created.",
                "data": {
                    "id": donation.id,
                    "alumni": donation.alumni.id,
                    "amount": donation.amount,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DonationDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, donation_id):
        return DonationService.get_donation_by_id(donation_id)

    @extend_schema(
        tags=["Alumni - Donations"],
        responses={200: DonationDetailResponseSerializer, 404: DonationDetailResponseSerializer},
        description="Retrieve a single donation record by ID."
    )
    def get(self, request, donation_id):
        donation = self.get_object(donation_id)
        if not donation:
            return Response({
                "status": False,
                "message": "Donation record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = DonationDisplaySerializer(donation, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Donation record retrieved.",
            "data": {"donation": data}
        })

    @extend_schema(
        tags=["Alumni - Donations"],
        request=DonationUpdateSerializer,
        responses={200: DonationUpdateResponseSerializer, 400: DonationUpdateResponseSerializer, 403: DonationUpdateResponseSerializer},
        description="Update a donation record."
    )
    @transaction.atomic
    def put(self, request, donation_id):
        return self._update(request, donation_id, partial=False)

    @extend_schema(
        tags=["Alumni - Donations"],
        request=DonationUpdateSerializer,
        responses={200: DonationUpdateResponseSerializer, 400: DonationUpdateResponseSerializer, 403: DonationUpdateResponseSerializer},
        description="Partially update a donation record."
    )
    @transaction.atomic
    def patch(self, request, donation_id):
        return self._update(request, donation_id, partial=True)

    def _update(self, request, donation_id, partial):
        donation = self.get_object(donation_id)
        if not donation:
            return Response({
                "status": False,
                "message": "Donation record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if not (user.is_staff or (donation.alumni.user and user == donation.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = DonationUpdateSerializer(donation, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = DonationDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Donation record updated.",
                "data": {"donation": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Alumni - Donations"],
        responses={200: DonationDeleteResponseSerializer, 403: DonationDeleteResponseSerializer, 404: DonationDeleteResponseSerializer},
        description="Delete a donation record (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, donation_id):
        donation = self.get_object(donation_id)
        if not donation:
            return Response({
                "status": False,
                "message": "Donation record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not (user.is_staff or (donation.alumni.user and user == donation.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = DonationService.delete_donation(donation)
        if success:
            return Response({
                "status": True,
                "message": "Donation record deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete donation record.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DonationStatisticsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni - Donations"],
        parameters=[
            OpenApiParameter(name="alumni_id", type=int, description="Alumni ID", required=True),
        ],
        responses={200: serializers.Serializer},
        description="Get total donation amount for an alumni."
    )
    def get(self, request):
        alumni_id = request.query_params.get("alumni_id")
        if not alumni_id:
            return Response({
                "status": False,
                "message": "alumni_id parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        total = DonationService.get_total_donations_by_alumni(alumni_id)
        return Response({
            "status": True,
            "message": "Total donations retrieved.",
            "data": {"total_donations": total}
        })