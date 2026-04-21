import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from facilities.models import FacilityReservation
from facilities.serializers.reservation import (
    FacilityReservationMinimalSerializer,
    FacilityReservationCreateSerializer,
    FacilityReservationUpdateSerializer,
    FacilityReservationDisplaySerializer,
)
from facilities.services.reservation import FacilityReservationService

logger = logging.getLogger(__name__)

def can_view_reservation(user, reservation):
    if user.is_staff:
        return True
    return reservation.reserved_by == user

def can_manage_reservation(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'FACILITIES_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ReservationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    facility = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()

class ReservationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationCreateResponseData(allow_null=True)

class ReservationUpdateResponseData(serializers.Serializer):
    reservation = FacilityReservationDisplaySerializer()

class ReservationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationUpdateResponseData(allow_null=True)

class ReservationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ReservationDetailResponseData(serializers.Serializer):
    reservation = FacilityReservationDisplaySerializer()

class ReservationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationDetailResponseData(allow_null=True)

class ReservationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = FacilityReservationMinimalSerializer(many=True)

class ReservationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationListResponseData()

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

class FacilityReservationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Facilities - Reservations"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="facility_id", type=int, description="Filter by facility ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by status", required=False),
            OpenApiParameter(name="upcoming", type=bool, description="Only upcoming reservations", required=False),
        ],
        responses={200: ReservationListResponseSerializer},
        description="List facility reservations (admins see all, regular users see their own)."
    )
    def get(self, request):
        user = request.user
        facility_id = request.query_params.get("facility_id")
        status_filter = request.query_params.get("status")
        upcoming = request.query_params.get("upcoming", "false").lower() == "true"

        if user.is_staff or can_manage_reservation(user):
            queryset = FacilityReservation.objects.all().select_related('facility', 'reserved_by', 'approved_by')
        else:
            queryset = FacilityReservation.objects.filter(reserved_by=user).select_related('facility')

        if facility_id:
            queryset = queryset.filter(facility_id=facility_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if upcoming:
            from django.utils import timezone
            queryset = queryset.filter(start_datetime__gte=timezone.now())

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, FacilityReservationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Reservations retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Facilities - Reservations"],
        request=FacilityReservationCreateSerializer,
        responses={201: ReservationCreateResponseSerializer, 400: ReservationCreateResponseSerializer, 403: ReservationCreateResponseSerializer},
        description="Create a new facility reservation (authenticated users)."
    )
    @transaction.atomic
    def post(self, request):
        # Set reserved_by to current user
        data = request.data.copy()
        data['reserved_by_id'] = request.user.id
        serializer = FacilityReservationCreateSerializer(data=data)
        if serializer.is_valid():
            reservation = serializer.save()
            return Response({
                "status": True,
                "message": "Reservation created.",
                "data": {
                    "id": reservation.id,
                    "facility": reservation.facility.id,
                    "title": reservation.title,
                    "status": reservation.status,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FacilityReservationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, reservation_id):
        try:
            return FacilityReservation.objects.select_related('facility', 'reserved_by', 'approved_by').get(id=reservation_id)
        except FacilityReservation.DoesNotExist:
            return None

    @extend_schema(
        tags=["Facilities - Reservations"],
        responses={200: ReservationDetailResponseSerializer, 404: ReservationDetailResponseSerializer, 403: ReservationDetailResponseSerializer},
        description="Retrieve a single reservation by ID."
    )
    def get(self, request, reservation_id):
        reservation = self.get_object(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_reservation(request.user, reservation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = FacilityReservationDisplaySerializer(reservation, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Reservation retrieved.",
            "data": {"reservation": data}
        })

    @extend_schema(
        tags=["Facilities - Reservations"],
        request=FacilityReservationUpdateSerializer,
        responses={200: ReservationUpdateResponseSerializer, 400: ReservationUpdateResponseSerializer, 403: ReservationUpdateResponseSerializer},
        description="Update a reservation (only allowed before approval, or by staff)."
    )
    @transaction.atomic
    def put(self, request, reservation_id):
        return self._update(request, reservation_id, partial=False)

    @extend_schema(
        tags=["Facilities - Reservations"],
        request=FacilityReservationUpdateSerializer,
        responses={200: ReservationUpdateResponseSerializer, 400: ReservationUpdateResponseSerializer, 403: ReservationUpdateResponseSerializer},
        description="Partially update a reservation."
    )
    @transaction.atomic
    def patch(self, request, reservation_id):
        return self._update(request, reservation_id, partial=True)

    def _update(self, request, reservation_id, partial):
        reservation = self.get_object(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Allow owner to edit only if still pending, otherwise staff only
        user = request.user
        if not (user.is_staff or can_manage_reservation(user) or (reservation.reserved_by == user and reservation.status == 'PND')):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = FacilityReservationUpdateSerializer(reservation, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = FacilityReservationDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Reservation updated.",
                "data": {"reservation": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Facilities - Reservations"],
        responses={200: ReservationDeleteResponseSerializer, 403: ReservationDeleteResponseSerializer, 404: ReservationDeleteResponseSerializer},
        description="Cancel/delete a reservation (owner or staff)."
    )
    @transaction.atomic
    def delete(self, request, reservation_id):
        reservation = self.get_object(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not (user.is_staff or can_manage_reservation(user) or reservation.reserved_by == user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = FacilityReservationService.delete_reservation(reservation)
        if success:
            return Response({
                "status": True,
                "message": "Reservation cancelled/deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete reservation.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FacilityReservationApproveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Facilities - Reservations"],
        responses={200: ReservationUpdateResponseSerializer, 403: ReservationUpdateResponseSerializer, 404: ReservationUpdateResponseSerializer},
        description="Approve a pending reservation (staff/facilities manager only)."
    )
    @transaction.atomic
    def post(self, request, reservation_id):
        if not can_manage_reservation(request.user):
            return Response({
                "status": False,
                "message": "Facilities manager or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        reservation = FacilityReservationService.get_reservation_by_id(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if reservation.status != 'PND':
            return Response({
                "status": False,
                "message": "Only pending reservations can be approved.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = FacilityReservationService.approve_reservation(reservation, request.user)
        data = FacilityReservationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Reservation approved.",
            "data": {"reservation": data}
        })


class FacilityReservationRejectView(APIView):
    permission_classes = [IsAuthenticated]

    class RejectSerializer(serializers.Serializer):
        reason = serializers.CharField()

    @extend_schema(
        tags=["Facilities - Reservations"],
        request=RejectSerializer,
        responses={200: ReservationUpdateResponseSerializer, 400: ReservationUpdateResponseSerializer, 403: ReservationUpdateResponseSerializer},
        description="Reject a pending reservation (staff/facilities manager only)."
    )
    @transaction.atomic
    def post(self, request, reservation_id):
        if not can_manage_reservation(request.user):
            return Response({
                "status": False,
                "message": "Facilities manager or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        reservation = FacilityReservationService.get_reservation_by_id(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if reservation.status != 'PND':
            return Response({
                "status": False,
                "message": "Only pending reservations can be rejected.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.RejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = FacilityReservationService.reject_reservation(reservation, serializer.validated_data['reason'])
        data = FacilityReservationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Reservation rejected.",
            "data": {"reservation": data}
        })


class FacilityReservationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    class CancelSerializer(serializers.Serializer):
        reason = serializers.CharField()

    @extend_schema(
        tags=["Facilities - Reservations"],
        request=CancelSerializer,
        responses={200: ReservationUpdateResponseSerializer, 400: ReservationUpdateResponseSerializer, 403: ReservationUpdateResponseSerializer},
        description="Cancel a reservation (owner or staff)."
    )
    @transaction.atomic
    def post(self, request, reservation_id):
        reservation = FacilityReservationService.get_reservation_by_id(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not (user.is_staff or can_manage_reservation(user) or reservation.reserved_by == user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.CancelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = FacilityReservationService.cancel_reservation(reservation, serializer.validated_data['reason'])
        data = FacilityReservationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Reservation cancelled.",
            "data": {"reservation": data}
        })