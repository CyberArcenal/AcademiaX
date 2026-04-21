import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from classes.models import Classroom
from classes.serializers.classroom import (
    ClassroomMinimalSerializer,
    ClassroomCreateSerializer,
    ClassroomUpdateSerializer,
    ClassroomDisplaySerializer,
)
from classes.services.classroom import ClassroomService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_classroom(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ClassroomCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    room_number = serializers.CharField()
    building = serializers.CharField()

class ClassroomCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ClassroomCreateResponseData(allow_null=True)

class ClassroomUpdateResponseData(serializers.Serializer):
    classroom = ClassroomDisplaySerializer()

class ClassroomUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ClassroomUpdateResponseData(allow_null=True)

class ClassroomDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ClassroomDetailResponseData(serializers.Serializer):
    classroom = ClassroomDisplaySerializer()

class ClassroomDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ClassroomDetailResponseData(allow_null=True)

class ClassroomListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ClassroomMinimalSerializer(many=True)

class ClassroomListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ClassroomListResponseData()

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

class ClassroomListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Classrooms"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="building", type=str, description="Filter by building", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active classrooms", required=False),
        ],
        responses={200: ClassroomListResponseSerializer},
        description="List classrooms, optionally filtered by building."
    )
    def get(self, request):
        building = request.query_params.get("building")
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if building:
            classrooms = ClassroomService.get_classrooms_by_building(building, active_only=active_only)
        else:
            classrooms = ClassroomService.get_all_classrooms(active_only=active_only)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(classrooms, request)
        data = wrap_paginated_data(paginator, page, request, ClassroomMinimalSerializer)
        return Response({
            "status": True,
            "message": "Classrooms retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Classes - Classrooms"],
        request=ClassroomCreateSerializer,
        responses={201: ClassroomCreateResponseSerializer, 400: ClassroomCreateResponseSerializer, 403: ClassroomCreateResponseSerializer},
        description="Create a new classroom (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_classroom(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = ClassroomCreateSerializer(data=request.data)
        if serializer.is_valid():
            classroom = serializer.save()
            return Response({
                "status": True,
                "message": "Classroom created.",
                "data": {
                    "id": classroom.id,
                    "room_number": classroom.room_number,
                    "building": classroom.building,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ClassroomDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, classroom_id):
        return ClassroomService.get_classroom_by_id(classroom_id)

    @extend_schema(
        tags=["Classes - Classrooms"],
        responses={200: ClassroomDetailResponseSerializer, 404: ClassroomDetailResponseSerializer},
        description="Retrieve a single classroom by ID."
    )
    def get(self, request, classroom_id):
        classroom = self.get_object(classroom_id)
        if not classroom:
            return Response({
                "status": False,
                "message": "Classroom not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = ClassroomDisplaySerializer(classroom, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Classroom retrieved.",
            "data": {"classroom": data}
        })

    @extend_schema(
        tags=["Classes - Classrooms"],
        request=ClassroomUpdateSerializer,
        responses={200: ClassroomUpdateResponseSerializer, 400: ClassroomUpdateResponseSerializer, 403: ClassroomUpdateResponseSerializer},
        description="Update a classroom (admin only)."
    )
    @transaction.atomic
    def put(self, request, classroom_id):
        return self._update(request, classroom_id, partial=False)

    @extend_schema(
        tags=["Classes - Classrooms"],
        request=ClassroomUpdateSerializer,
        responses={200: ClassroomUpdateResponseSerializer, 400: ClassroomUpdateResponseSerializer, 403: ClassroomUpdateResponseSerializer},
        description="Partially update a classroom."
    )
    @transaction.atomic
    def patch(self, request, classroom_id):
        return self._update(request, classroom_id, partial=True)

    def _update(self, request, classroom_id, partial):
        if not can_manage_classroom(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        classroom = self.get_object(classroom_id)
        if not classroom:
            return Response({
                "status": False,
                "message": "Classroom not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ClassroomUpdateSerializer(classroom, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ClassroomDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Classroom updated.",
                "data": {"classroom": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Classes - Classrooms"],
        responses={200: ClassroomDeleteResponseSerializer, 403: ClassroomDeleteResponseSerializer, 404: ClassroomDeleteResponseSerializer},
        description="Delete a classroom (admin only)."
    )
    @transaction.atomic
    def delete(self, request, classroom_id):
        if not can_manage_classroom(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        classroom = self.get_object(classroom_id)
        if not classroom:
            return Response({
                "status": False,
                "message": "Classroom not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = ClassroomService.delete_classroom(classroom)
        if success:
            return Response({
                "status": True,
                "message": "Classroom deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete classroom.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClassroomAvailabilityView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Classrooms"],
        parameters=[
            OpenApiParameter(name="time_slot_id", type=int, description="Time slot ID", required=False),
            OpenApiParameter(name="date", type=str, description="Date (YYYY-MM-DD)", required=False),
        ],
        responses={200: serializers.Serializer},
        description="Get available classrooms for a given time slot and date."
    )
    def get(self, request):
        time_slot_id = request.query_params.get("time_slot_id")
        date_str = request.query_params.get("date")
        from datetime import datetime
        date = None
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Invalid date format. Use YYYY-MM-DD.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
        available = ClassroomService.get_available_classrooms(time_slot_id, date)
        data = [
            {
                "id": c.id,
                "room_number": c.room_number,
                "building": c.building,
                "capacity": c.capacity,
            }
            for c in available
        ]
        return Response({
            "status": True,
            "message": "Available classrooms retrieved.",
            "data": data
        })