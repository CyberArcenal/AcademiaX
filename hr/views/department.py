import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from hr.models import Department
from hr.serializers.department import (
    DepartmentMinimalSerializer,
    DepartmentCreateSerializer,
    DepartmentUpdateSerializer,
    DepartmentDisplaySerializer,
)
from hr.services.department import DepartmentService

logger = logging.getLogger(__name__)

def can_manage_department(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class DepartmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()

class DepartmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DepartmentCreateResponseData(allow_null=True)

class DepartmentUpdateResponseData(serializers.Serializer):
    department = DepartmentDisplaySerializer()

class DepartmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DepartmentUpdateResponseData(allow_null=True)

class DepartmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class DepartmentDetailResponseData(serializers.Serializer):
    department = DepartmentDisplaySerializer()

class DepartmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DepartmentDetailResponseData(allow_null=True)

class DepartmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = DepartmentMinimalSerializer(many=True)

class DepartmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = DepartmentListResponseData()

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

class DepartmentListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["HR - Departments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: DepartmentListResponseSerializer},
        description="List departments."
    )
    def get(self, request):
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        departments = DepartmentService.get_all_departments(active_only=active_only)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(departments, request)
        data = wrap_paginated_data(paginator, page, request, DepartmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Departments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Departments"],
        request=DepartmentCreateSerializer,
        responses={201: DepartmentCreateResponseSerializer, 400: DepartmentCreateResponseSerializer, 403: DepartmentCreateResponseSerializer},
        description="Create a new department (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_department(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = DepartmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            department = serializer.save()
            return Response({
                "status": True,
                "message": "Department created.",
                "data": {
                    "id": department.id,
                    "name": department.name,
                    "code": department.code,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DepartmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, dept_id):
        return DepartmentService.get_department_by_id(dept_id)

    @extend_schema(
        tags=["HR - Departments"],
        responses={200: DepartmentDetailResponseSerializer, 404: DepartmentDetailResponseSerializer},
        description="Retrieve a single department by ID."
    )
    def get(self, request, dept_id):
        department = self.get_object(dept_id)
        if not department:
            return Response({
                "status": False,
                "message": "Department not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = DepartmentDisplaySerializer(department, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Department retrieved.",
            "data": {"department": data}
        })

    @extend_schema(
        tags=["HR - Departments"],
        request=DepartmentUpdateSerializer,
        responses={200: DepartmentUpdateResponseSerializer, 400: DepartmentUpdateResponseSerializer, 403: DepartmentUpdateResponseSerializer},
        description="Update a department (admin/hr only)."
    )
    @transaction.atomic
    def put(self, request, dept_id):
        return self._update(request, dept_id, partial=False)

    @extend_schema(
        tags=["HR - Departments"],
        request=DepartmentUpdateSerializer,
        responses={200: DepartmentUpdateResponseSerializer, 400: DepartmentUpdateResponseSerializer, 403: DepartmentUpdateResponseSerializer},
        description="Partially update a department."
    )
    @transaction.atomic
    def patch(self, request, dept_id):
        return self._update(request, dept_id, partial=True)

    def _update(self, request, dept_id, partial):
        if not can_manage_department(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        department = self.get_object(dept_id)
        if not department:
            return Response({
                "status": False,
                "message": "Department not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = DepartmentUpdateSerializer(department, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = DepartmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Department updated.",
                "data": {"department": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["HR - Departments"],
        responses={200: DepartmentDeleteResponseSerializer, 403: DepartmentDeleteResponseSerializer, 404: DepartmentDeleteResponseSerializer},
        description="Delete a department (admin/hr only)."
    )
    @transaction.atomic
    def delete(self, request, dept_id):
        if not can_manage_department(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        department = self.get_object(dept_id)
        if not department:
            return Response({
                "status": False,
                "message": "Department not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = DepartmentService.delete_department(department)
        if success:
            return Response({
                "status": True,
                "message": "Department deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete department.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)