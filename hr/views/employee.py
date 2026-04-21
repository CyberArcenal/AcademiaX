import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from hr.models import Employee
from hr.serializers.employee import (
    EmployeeMinimalSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    EmployeeDisplaySerializer,
)
from hr.services.employee import EmployeeService

logger = logging.getLogger(__name__)

def can_view_employee(user, employee):
    if user.is_staff:
        return True
    if user.role in ['ADMIN', 'HR_MANAGER']:
        return True
    # Employees can view their own record
    if user.role == 'EMPLOYEE' and hasattr(user, 'employee_record'):
        return employee == user.employee_record
    return False

def can_manage_employee(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER'])

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class EmployeeCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    employee_number = serializers.CharField()
    user = serializers.IntegerField()

class EmployeeCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmployeeCreateResponseData(allow_null=True)

class EmployeeUpdateResponseData(serializers.Serializer):
    employee = EmployeeDisplaySerializer()

class EmployeeUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmployeeUpdateResponseData(allow_null=True)

class EmployeeDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EmployeeDetailResponseData(serializers.Serializer):
    employee = EmployeeDisplaySerializer()

class EmployeeDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmployeeDetailResponseData(allow_null=True)

class EmployeeListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EmployeeMinimalSerializer(many=True)

class EmployeeListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EmployeeListResponseData()

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

class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Employees"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="department_id", type=int, description="Filter by department ID", required=False),
            OpenApiParameter(name="status", type=str, description="Filter by employment status", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active employees", required=False),
        ],
        responses={200: EmployeeListResponseSerializer},
        description="List employees (admins/hr see all, employees see only their own)."
    )
    def get(self, request):
        user = request.user
        department_id = request.query_params.get("department_id")
        status_filter = request.query_params.get("status")
        active_only = request.query_params.get("active_only", "false").lower() == "true"

        if user.is_staff or can_manage_employee(user):
            queryset = Employee.objects.all().select_related('user', 'department', 'position', 'supervisor')
        else:
            # Regular employees see only their own record
            if hasattr(user, 'employee_record'):
                queryset = Employee.objects.filter(id=user.employee_record.id)
            else:
                return Response({
                    "status": False,
                    "message": "Employee record not found for this user.",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if active_only:
            queryset = queryset.filter(status='ACT')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, EmployeeMinimalSerializer)
        return Response({
            "status": True,
            "message": "Employees retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Employees"],
        request=EmployeeCreateSerializer,
        responses={201: EmployeeCreateResponseSerializer, 400: EmployeeCreateResponseSerializer, 403: EmployeeCreateResponseSerializer},
        description="Create a new employee record (admin/hr only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_employee(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = EmployeeCreateSerializer(data=request.data)
        if serializer.is_valid():
            employee = serializer.save()
            return Response({
                "status": True,
                "message": "Employee created.",
                "data": {
                    "id": employee.id,
                    "employee_number": employee.employee_number,
                    "user": employee.user.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, employee_id):
        try:
            return Employee.objects.select_related('user', 'department', 'position', 'supervisor').get(id=employee_id)
        except Employee.DoesNotExist:
            return None

    @extend_schema(
        tags=["HR - Employees"],
        responses={200: EmployeeDetailResponseSerializer, 404: EmployeeDetailResponseSerializer, 403: EmployeeDetailResponseSerializer},
        description="Retrieve a single employee by ID."
    )
    def get(self, request, employee_id):
        employee = self.get_object(employee_id)
        if not employee:
            return Response({
                "status": False,
                "message": "Employee not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_employee(request.user, employee):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = EmployeeDisplaySerializer(employee, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Employee retrieved.",
            "data": {"employee": data}
        })

    @extend_schema(
        tags=["HR - Employees"],
        request=EmployeeUpdateSerializer,
        responses={200: EmployeeUpdateResponseSerializer, 400: EmployeeUpdateResponseSerializer, 403: EmployeeUpdateResponseSerializer},
        description="Update an employee record (admin/hr only)."
    )
    @transaction.atomic
    def put(self, request, employee_id):
        return self._update(request, employee_id, partial=False)

    @extend_schema(
        tags=["HR - Employees"],
        request=EmployeeUpdateSerializer,
        responses={200: EmployeeUpdateResponseSerializer, 400: EmployeeUpdateResponseSerializer, 403: EmployeeUpdateResponseSerializer},
        description="Partially update an employee record."
    )
    @transaction.atomic
    def patch(self, request, employee_id):
        return self._update(request, employee_id, partial=True)

    def _update(self, request, employee_id, partial):
        if not can_manage_employee(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        employee = self.get_object(employee_id)
        if not employee:
            return Response({
                "status": False,
                "message": "Employee not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeUpdateSerializer(employee, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = EmployeeDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Employee updated.",
                "data": {"employee": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["HR - Employees"],
        responses={200: EmployeeDeleteResponseSerializer, 403: EmployeeDeleteResponseSerializer, 404: EmployeeDeleteResponseSerializer},
        description="Delete an employee record (admin/hr only)."
    )
    @transaction.atomic
    def delete(self, request, employee_id):
        if not can_manage_employee(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        employee = self.get_object(employee_id)
        if not employee:
            return Response({
                "status": False,
                "message": "Employee not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = EmployeeService.delete_employee(employee)
        if success:
            return Response({
                "status": True,
                "message": "Employee deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete employee.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Employees"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: EmployeeListResponseSerializer},
        description="Search employees by name or employee number (admin/hr only)."
    )
    def get(self, request):
        if not can_manage_employee(request.user):
            return Response({
                "status": False,
                "message": "Admin or HR permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        employees = EmployeeService.search_employees(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(employees, request)
        data = wrap_paginated_data(paginator, page, request, EmployeeMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })