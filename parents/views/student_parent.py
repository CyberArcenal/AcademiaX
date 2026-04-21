import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from parents.models import StudentParent
from parents.serializers.student_parent import (
    StudentParentMinimalSerializer,
    StudentParentCreateSerializer,
    StudentParentUpdateSerializer,
    StudentParentDisplaySerializer,
)
from parents.services.student_parent import StudentParentService

logger = logging.getLogger(__name__)

def can_view_relationship(user, relationship):
    if user.is_staff:
        return True
    if user.role == 'PARENT' and hasattr(user, 'parent_profile'):
        return relationship.parent == user.parent_profile
    if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
        return relationship.student == user.student_profile
    return False

def can_manage_relationship(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'REGISTRAR'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class StudentParentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    student = serializers.IntegerField()
    parent = serializers.IntegerField()
    relationship = serializers.CharField()

class StudentParentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentParentCreateResponseData(allow_null=True)

class StudentParentUpdateResponseData(serializers.Serializer):
    relationship = StudentParentDisplaySerializer()

class StudentParentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentParentUpdateResponseData(allow_null=True)

class StudentParentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class StudentParentDetailResponseData(serializers.Serializer):
    relationship = StudentParentDisplaySerializer()

class StudentParentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentParentDetailResponseData(allow_null=True)

class StudentParentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = StudentParentMinimalSerializer(many=True)

class StudentParentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = StudentParentListResponseData()

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

class StudentParentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Parents - Student Relationships"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="student_id", type=int, description="Filter by student ID", required=False),
            OpenApiParameter(name="parent_id", type=int, description="Filter by parent ID", required=False),
        ],
        responses={200: StudentParentListResponseSerializer},
        description="List student-parent relationships (filtered by role)."
    )
    def get(self, request):
        user = request.user
        student_id = request.query_params.get("student_id")
        parent_id = request.query_params.get("parent_id")

        if user.is_staff or can_manage_relationship(user):
            queryset = StudentParent.objects.all().select_related('student', 'parent')
        else:
            if user.role == 'STUDENT' and hasattr(user, 'student_profile'):
                queryset = StudentParent.objects.filter(student=user.student_profile)
            elif user.role == 'PARENT' and hasattr(user, 'parent_profile'):
                queryset = StudentParent.objects.filter(parent=user.parent_profile)
            else:
                return Response({
                    "status": False,
                    "message": "Permission denied.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, StudentParentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Student-parent relationships retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Parents - Student Relationships"],
        request=StudentParentCreateSerializer,
        responses={201: StudentParentCreateResponseSerializer, 400: StudentParentCreateResponseSerializer, 403: StudentParentCreateResponseSerializer},
        description="Create a student-parent relationship (admin/registrar only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_relationship(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = StudentParentCreateSerializer(data=request.data)
        if serializer.is_valid():
            relationship = serializer.save()
            return Response({
                "status": True,
                "message": "Relationship created.",
                "data": {
                    "id": relationship.id,
                    "student": relationship.student.id,
                    "parent": relationship.parent.id,
                    "relationship": relationship.relationship,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentParentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, rel_id):
        try:
            return StudentParent.objects.select_related('student', 'parent').get(id=rel_id)
        except StudentParent.DoesNotExist:
            return None

    @extend_schema(
        tags=["Parents - Student Relationships"],
        responses={200: StudentParentDetailResponseSerializer, 404: StudentParentDetailResponseSerializer, 403: StudentParentDetailResponseSerializer},
        description="Retrieve a single student-parent relationship by ID."
    )
    def get(self, request, rel_id):
        relationship = self.get_object(rel_id)
        if not relationship:
            return Response({
                "status": False,
                "message": "Relationship not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_relationship(request.user, relationship):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = StudentParentDisplaySerializer(relationship, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Relationship retrieved.",
            "data": {"relationship": data}
        })

    @extend_schema(
        tags=["Parents - Student Relationships"],
        request=StudentParentUpdateSerializer,
        responses={200: StudentParentUpdateResponseSerializer, 400: StudentParentUpdateResponseSerializer, 403: StudentParentUpdateResponseSerializer},
        description="Update a student-parent relationship (admin/registrar only)."
    )
    @transaction.atomic
    def put(self, request, rel_id):
        return self._update(request, rel_id, partial=False)

    @extend_schema(
        tags=["Parents - Student Relationships"],
        request=StudentParentUpdateSerializer,
        responses={200: StudentParentUpdateResponseSerializer, 400: StudentParentUpdateResponseSerializer, 403: StudentParentUpdateResponseSerializer},
        description="Partially update a student-parent relationship."
    )
    @transaction.atomic
    def patch(self, request, rel_id):
        return self._update(request, rel_id, partial=True)

    def _update(self, request, rel_id, partial):
        if not can_manage_relationship(request.user):
            return Response({
                "status": False,
                "message": "Admin or registrar permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        relationship = self.get_object(rel_id)
        if not relationship:
            return Response({
                "status": False,
                "message": "Relationship not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentParentUpdateSerializer(relationship, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = StudentParentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Relationship updated.",
                "data": {"relationship": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Parents - Student Relationships"],
        responses={200: StudentParentDeleteResponseSerializer, 403: StudentParentDeleteResponseSerializer, 404: StudentParentDeleteResponseSerializer},
        description="Delete a student-parent relationship (admin only)."
    )
    @transaction.atomic
    def delete(self, request, rel_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        relationship = self.get_object(rel_id)
        if not relationship:
            return Response({
                "status": False,
                "message": "Relationship not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = StudentParentService.delete_relationship(relationship)
        if success:
            return Response({
                "status": True,
                "message": "Relationship deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete relationship.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)