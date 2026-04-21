import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from library.models import Reservation
from library.serializers.reservation import (
    ReservationMinimalSerializer,
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationDisplaySerializer,
)
from library.services.reservation import ReservationService
from library.services.copy import BookCopyService

logger = logging.getLogger(__name__)

def can_view_reservation(user, reservation):
    if user.is_staff:
        return True
    # Students can see their own reservations
    if hasattr(user, 'student_profile'):
        return reservation.student == user.student_profile
    return False

def can_manage_reservation(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'LIBRARIAN'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ReservationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    copy = serializers.IntegerField()
    student = serializers.IntegerField()
    expiry_date = serializers.DateField()

class ReservationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationCreateResponseData(allow_null=True)

class ReservationUpdateResponseData(serializers.Serializer):
    reservation = ReservationDisplaySerializer()

class ReservationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationUpdateResponseData(allow_null=True)

class ReservationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ReservationDetailResponseData(serializers.Serializer):
    reservation = ReservationDisplaySerializer()

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
    results = ReservationMinimalSerializer(many=True)

class ReservationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationListResponseData()

class ReservationCancelResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ReservationDisplaySerializer()

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

class ReservationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Library - Reservations"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active reservations", required=False),
        ],
        responses={200: ReservationListResponseSerializer},
        description="List reservations (admins/librarians see all, students see their own)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        if user.is_staff or can_manage_reservation(user):
            queryset = Reservation.objects.all().select_related('copy', 'student')
        else:
            if hasattr(user, 'student_profile'):
                queryset = Reservation.objects.filter(student=user.student_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if active_only:
            queryset = queryset.filter(is_active=True)

        queryset = queryset.order_by('-reservation_date')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, ReservationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Reservations retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Library - Reservations"],
        request=ReservationCreateSerializer,
        responses={201: ReservationCreateResponseSerializer, 400: ReservationCreateResponseSerializer, 403: ReservationCreateResponseSerializer},
        description="Create a reservation (students can reserve for themselves)."
    )
    @transaction.atomic
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # For students, set student_id to their own profile
        data = request.data.copy()
        if not can_manage_reservation(request.user):
            if hasattr(request.user, 'student_profile'):
                data['student_id'] = request.user.student_profile.id
            else:
                return Response({
                    "status": False,
                    "message": "Student profile not found.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        serializer = ReservationCreateSerializer(data=data)
        if serializer.is_valid():
            reservation = serializer.save()
            return Response({
                "status": True,
                "message": "Reservation created.",
                "data": {
                    "id": reservation.id,
                    "copy": reservation.copy.id,
                    "student": reservation.student.id,
                    "expiry_date": reservation.expiry_date,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReservationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, reservation_id):
        try:
            return Reservation.objects.select_related('copy', 'student').get(id=reservation_id)
        except Reservation.DoesNotExist:
            return None

    @extend_schema(
        tags=["Library - Reservations"],
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
        data = ReservationDisplaySerializer(reservation, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Reservation retrieved.",
            "data": {"reservation": data}
        })

    @extend_schema(
        tags=["Library - Reservations"],
        request=ReservationUpdateSerializer,
        responses={200: ReservationUpdateResponseSerializer, 400: ReservationUpdateResponseSerializer, 403: ReservationUpdateResponseSerializer},
        description="Update a reservation (e.g., expiry date)."
    )
    @transaction.atomic
    def put(self, request, reservation_id):
        return self._update(request, reservation_id, partial=False)

    @extend_schema(
        tags=["Library - Reservations"],
        request=ReservationUpdateSerializer,
        responses={200: ReservationUpdateResponseSerializer, 400: ReservationUpdateResponseSerializer, 403: ReservationUpdateResponseSerializer},
        description="Partially update a reservation."
    )
    @transaction.atomic
    def patch(self, request, reservation_id):
        return self._update(request, reservation_id, partial=True)

    def _update(self, request, reservation_id, partial):
        if not can_manage_reservation(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        reservation = self.get_object(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ReservationUpdateSerializer(reservation, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ReservationDisplaySerializer(updated, context={"request": request}).data
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
        tags=["Library - Reservations"],
        responses={200: ReservationDeleteResponseSerializer, 403: ReservationDeleteResponseSerializer, 404: ReservationDeleteResponseSerializer},
        description="Delete a reservation (admin only)."
    )
    @transaction.atomic
    def delete(self, request, reservation_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        reservation = self.get_object(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ReservationService.delete_reservation(reservation)
        if success:
            return Response({
                "status": True,
                "message": "Reservation deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete reservation.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReservationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Library - Reservations"],
        responses={200: ReservationCancelResponseSerializer, 403: ReservationCancelResponseSerializer, 404: ReservationCancelResponseSerializer},
        description="Cancel a reservation (student can cancel their own, librarian can cancel any)."
    )
    @transaction.atomic
    def post(self, request, reservation_id):
        reservation = ReservationService.get_reservation_by_id(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not (user.is_staff or can_manage_reservation(user) or (hasattr(user, 'student_profile') and reservation.student == user.student_profile)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if not reservation.is_active:
            return Response({
                "status": False,
                "message": "Reservation is already cancelled or fulfilled.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = ReservationService.cancel_reservation(reservation)
        data = ReservationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Reservation cancelled.",
            "data": {"reservation": data}
        })


class ReservationFulfillView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Library - Reservations"],
        responses={200: ReservationCancelResponseSerializer, 403: ReservationCancelResponseSerializer, 404: ReservationCancelResponseSerializer},
        description="Mark a reservation as fulfilled (when student borrows the book). Librarian only."
    )
    @transaction.atomic
    def post(self, request, reservation_id):
        if not can_manage_reservation(request.user):
            return Response({
                "status": False,
                "message": "Librarian or admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        reservation = ReservationService.get_reservation_by_id(reservation_id)
        if not reservation:
            return Response({
                "status": False,
                "message": "Reservation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not reservation.is_active:
            return Response({
                "status": False,
                "message": "Reservation is not active.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = ReservationService.fulfill_reservation(reservation)
        data = ReservationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Reservation marked as fulfilled.",
            "data": {"reservation": data}
        })