import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from attendance.models import Holiday
from attendance.serializers.holiday import (
    HolidayMinimalSerializer,
    HolidayCreateSerializer,
    HolidayUpdateSerializer,
    HolidayDisplaySerializer,
)
from attendance.services.holiday import HolidayService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# Helper to check if user can manage holidays (admin only)
def can_manage_holidays(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class HolidayCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    date = serializers.DateField()

class HolidayCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = HolidayCreateResponseData(allow_null=True)

class HolidayUpdateResponseData(serializers.Serializer):
    holiday = HolidayDisplaySerializer()

class HolidayUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = HolidayUpdateResponseData(allow_null=True)

class HolidayDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class HolidayDetailResponseData(serializers.Serializer):
    holiday = HolidayDisplaySerializer()

class HolidayDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = HolidayDetailResponseData(allow_null=True)

class HolidayListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = HolidayMinimalSerializer(many=True)

class HolidayListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = HolidayListResponseData()

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

class HolidayListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Attendance - Holidays"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="year", type=int, description="Filter by year", required=False),
            OpenApiParameter(name="upcoming", type=bool, description="Show upcoming holidays (within 30 days)", required=False),
        ],
        responses={200: HolidayListResponseSerializer},
        description="List holidays. Public endpoint."
    )
    def get(self, request):
        year = request.query_params.get("year")
        upcoming = request.query_params.get("upcoming", "false").lower() == "true"
        if upcoming:
            holidays = HolidayService.get_upcoming_holidays()
        elif year:
            holidays = HolidayService.get_all_holidays(year=year)
        else:
            holidays = HolidayService.get_all_holidays()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(holidays, request)
        data = wrap_paginated_data(paginator, page, request, HolidayMinimalSerializer)
        return Response({
            "status": True,
            "message": "Holidays retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Attendance - Holidays"],
        request=HolidayCreateSerializer,
        responses={201: HolidayCreateResponseSerializer, 400: HolidayCreateResponseSerializer, 403: HolidayCreateResponseSerializer},
        description="Create a new holiday (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_holidays(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = HolidayCreateSerializer(data=request.data)
        if serializer.is_valid():
            holiday = serializer.save()
            return Response({
                "status": True,
                "message": "Holiday created.",
                "data": {
                    "id": holiday.id,
                    "name": holiday.name,
                    "date": holiday.date,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class HolidayDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, holiday_id):
        return HolidayService.get_holiday_by_id(holiday_id)

    @extend_schema(
        tags=["Attendance - Holidays"],
        responses={200: HolidayDetailResponseSerializer, 404: HolidayDetailResponseSerializer},
        description="Retrieve a single holiday by ID."
    )
    def get(self, request, holiday_id):
        holiday = self.get_object(holiday_id)
        if not holiday:
            return Response({
                "status": False,
                "message": "Holiday not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = HolidayDisplaySerializer(holiday, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Holiday retrieved.",
            "data": {"holiday": data}
        })

    @extend_schema(
        tags=["Attendance - Holidays"],
        request=HolidayUpdateSerializer,
        responses={200: HolidayUpdateResponseSerializer, 400: HolidayUpdateResponseSerializer, 403: HolidayUpdateResponseSerializer},
        description="Update a holiday (admin only)."
    )
    @transaction.atomic
    def put(self, request, holiday_id):
        return self._update(request, holiday_id, partial=False)

    @extend_schema(
        tags=["Attendance - Holidays"],
        request=HolidayUpdateSerializer,
        responses={200: HolidayUpdateResponseSerializer, 400: HolidayUpdateResponseSerializer, 403: HolidayUpdateResponseSerializer},
        description="Partially update a holiday (admin only)."
    )
    @transaction.atomic
    def patch(self, request, holiday_id):
        return self._update(request, holiday_id, partial=True)

    def _update(self, request, holiday_id, partial):
        if not can_manage_holidays(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        holiday = self.get_object(holiday_id)
        if not holiday:
            return Response({
                "status": False,
                "message": "Holiday not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = HolidayUpdateSerializer(holiday, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = HolidayDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Holiday updated.",
                "data": {"holiday": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Attendance - Holidays"],
        responses={200: HolidayDeleteResponseSerializer, 403: HolidayDeleteResponseSerializer, 404: HolidayDeleteResponseSerializer},
        description="Delete a holiday (admin only)."
    )
    @transaction.atomic
    def delete(self, request, holiday_id):
        if not can_manage_holidays(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        holiday = self.get_object(holiday_id)
        if not holiday:
            return Response({
                "status": False,
                "message": "Holiday not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        success = HolidayService.delete_holiday(holiday)
        if success:
            return Response({
                "status": True,
                "message": "Holiday deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete holiday.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HolidayCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Attendance - Holidays"],
        parameters=[
            OpenApiParameter(name="date", type=str, description="Date to check (YYYY-MM-DD)", required=True),
        ],
        responses={200: serializers.Serializer},
        description="Check if a specific date is a holiday."
    )
    def get(self, request):
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({
                "status": False,
                "message": "date parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            from datetime import datetime
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "status": False,
                "message": "Invalid date format. Use YYYY-MM-DD.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        is_holiday = HolidayService.is_holiday(date)
        return Response({
            "status": True,
            "message": "Holiday check completed.",
            "data": {"date": date_str, "is_holiday": is_holiday}
        })