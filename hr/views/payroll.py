import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from hr.models import SalaryGrade, PayrollPeriod
from hr.serializers.payroll import (
    SalaryGradeMinimalSerializer,
    SalaryGradeCreateSerializer,
    SalaryGradeUpdateSerializer,
    SalaryGradeDisplaySerializer,
    PayrollPeriodMinimalSerializer,
    PayrollPeriodCreateSerializer,
    PayrollPeriodUpdateSerializer,
    PayrollPeriodDisplaySerializer,
)
from hr.services.payroll import SalaryGradeService, PayrollPeriodService

logger = logging.getLogger(__name__)

def can_manage_payroll(user):
    return user.is_authenticated and (user.is_staff or user.role in ['ADMIN', 'HR_MANAGER', 'ACCOUNTING'])

# ----------------------------------------------------------------------
# Response serializers for SalaryGrade
# ----------------------------------------------------------------------

class SalaryGradeCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    grade = serializers.IntegerField()
    basic_salary = serializers.DecimalField(max_digits=12, decimal_places=2)

class SalaryGradeCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SalaryGradeCreateResponseData(allow_null=True)

class SalaryGradeUpdateResponseData(serializers.Serializer):
    salary_grade = SalaryGradeDisplaySerializer()

class SalaryGradeUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SalaryGradeUpdateResponseData(allow_null=True)

class SalaryGradeDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class SalaryGradeDetailResponseData(serializers.Serializer):
    salary_grade = SalaryGradeDisplaySerializer()

class SalaryGradeDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SalaryGradeDetailResponseData(allow_null=True)

class SalaryGradeListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SalaryGradeMinimalSerializer(many=True)

class SalaryGradeListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = SalaryGradeListResponseData()

# ----------------------------------------------------------------------
# Response serializers for PayrollPeriod
# ----------------------------------------------------------------------

class PayrollPeriodCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

class PayrollPeriodCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayrollPeriodCreateResponseData(allow_null=True)

class PayrollPeriodUpdateResponseData(serializers.Serializer):
    period = PayrollPeriodDisplaySerializer()

class PayrollPeriodUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayrollPeriodUpdateResponseData(allow_null=True)

class PayrollPeriodDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class PayrollPeriodDetailResponseData(serializers.Serializer):
    period = PayrollPeriodDisplaySerializer()

class PayrollPeriodDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayrollPeriodDetailResponseData(allow_null=True)

class PayrollPeriodListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PayrollPeriodMinimalSerializer(many=True)

class PayrollPeriodListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PayrollPeriodListResponseData()

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
# SalaryGrade Views
# ----------------------------------------------------------------------

class SalaryGradeListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Payroll (Salary Grades)"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: SalaryGradeListResponseSerializer},
        description="List salary grades (admin/hr/accounting only)."
    )
    def get(self, request):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        grades = SalaryGrade.objects.all().order_by('grade')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(grades, request)
        data = wrap_paginated_data(paginator, page, request, SalaryGradeMinimalSerializer)
        return Response({
            "status": True,
            "message": "Salary grades retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Payroll (Salary Grades)"],
        request=SalaryGradeCreateSerializer,
        responses={201: SalaryGradeCreateResponseSerializer, 400: SalaryGradeCreateResponseSerializer, 403: SalaryGradeCreateResponseSerializer},
        description="Create a salary grade (admin/hr/accounting only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = SalaryGradeCreateSerializer(data=request.data)
        if serializer.is_valid():
            sg = serializer.save()
            return Response({
                "status": True,
                "message": "Salary grade created.",
                "data": {
                    "id": sg.id,
                    "grade": sg.grade,
                    "basic_salary": sg.basic_salary,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SalaryGradeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, grade_id):
        return SalaryGradeService.get_salary_grade_by_id(grade_id)

    @extend_schema(
        tags=["HR - Payroll (Salary Grades)"],
        responses={200: SalaryGradeDetailResponseSerializer, 404: SalaryGradeDetailResponseSerializer, 403: SalaryGradeDetailResponseSerializer},
        description="Retrieve a salary grade by ID."
    )
    def get(self, request, grade_id):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        sg = self.get_object(grade_id)
        if not sg:
            return Response({
                "status": False,
                "message": "Salary grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = SalaryGradeDisplaySerializer(sg, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Salary grade retrieved.",
            "data": {"salary_grade": data}
        })

    @extend_schema(
        tags=["HR - Payroll (Salary Grades)"],
        request=SalaryGradeUpdateSerializer,
        responses={200: SalaryGradeUpdateResponseSerializer, 400: SalaryGradeUpdateResponseSerializer, 403: SalaryGradeUpdateResponseSerializer},
        description="Update a salary grade."
    )
    @transaction.atomic
    def put(self, request, grade_id):
        return self._update(request, grade_id, partial=False)

    @extend_schema(
        tags=["HR - Payroll (Salary Grades)"],
        request=SalaryGradeUpdateSerializer,
        responses={200: SalaryGradeUpdateResponseSerializer, 400: SalaryGradeUpdateResponseSerializer, 403: SalaryGradeUpdateResponseSerializer},
        description="Partially update a salary grade."
    )
    @transaction.atomic
    def patch(self, request, grade_id):
        return self._update(request, grade_id, partial=True)

    def _update(self, request, grade_id, partial):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        sg = self.get_object(grade_id)
        if not sg:
            return Response({
                "status": False,
                "message": "Salary grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = SalaryGradeUpdateSerializer(sg, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = SalaryGradeDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Salary grade updated.",
                "data": {"salary_grade": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["HR - Payroll (Salary Grades)"],
        responses={200: SalaryGradeDeleteResponseSerializer, 403: SalaryGradeDeleteResponseSerializer, 404: SalaryGradeDeleteResponseSerializer},
        description="Delete a salary grade."
    )
    @transaction.atomic
    def delete(self, request, grade_id):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        sg = self.get_object(grade_id)
        if not sg:
            return Response({
                "status": False,
                "message": "Salary grade not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = SalaryGradeService.delete_salary_grade(sg)
        if success:
            return Response({
                "status": True,
                "message": "Salary grade deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete salary grade.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ----------------------------------------------------------------------
# PayrollPeriod Views
# ----------------------------------------------------------------------

class PayrollPeriodListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="is_closed", type=bool, description="Filter by closed status", required=False),
        ],
        responses={200: PayrollPeriodListResponseSerializer},
        description="List payroll periods."
    )
    def get(self, request):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        queryset = PayrollPeriod.objects.all().order_by('-start_date')
        is_closed = request.query_params.get("is_closed")
        if is_closed is not None:
            closed = is_closed.lower() == "true"
            queryset = queryset.filter(is_closed=closed)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, PayrollPeriodMinimalSerializer)
        return Response({
            "status": True,
            "message": "Payroll periods retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        request=PayrollPeriodCreateSerializer,
        responses={201: PayrollPeriodCreateResponseSerializer, 400: PayrollPeriodCreateResponseSerializer, 403: PayrollPeriodCreateResponseSerializer},
        description="Create a payroll period."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = PayrollPeriodCreateSerializer(data=request.data)
        if serializer.is_valid():
            period = serializer.save()
            return Response({
                "status": True,
                "message": "Payroll period created.",
                "data": {
                    "id": period.id,
                    "name": period.name,
                    "start_date": period.start_date,
                    "end_date": period.end_date,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PayrollPeriodDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, period_id):
        return PayrollPeriodService.get_payroll_period_by_id(period_id)

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        responses={200: PayrollPeriodDetailResponseSerializer, 404: PayrollPeriodDetailResponseSerializer, 403: PayrollPeriodDetailResponseSerializer},
        description="Retrieve a payroll period by ID."
    )
    def get(self, request, period_id):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        period = self.get_object(period_id)
        if not period:
            return Response({
                "status": False,
                "message": "Payroll period not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = PayrollPeriodDisplaySerializer(period, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Payroll period retrieved.",
            "data": {"period": data}
        })

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        request=PayrollPeriodUpdateSerializer,
        responses={200: PayrollPeriodUpdateResponseSerializer, 400: PayrollPeriodUpdateResponseSerializer, 403: PayrollPeriodUpdateResponseSerializer},
        description="Update a payroll period."
    )
    @transaction.atomic
    def put(self, request, period_id):
        return self._update(request, period_id, partial=False)

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        request=PayrollPeriodUpdateSerializer,
        responses={200: PayrollPeriodUpdateResponseSerializer, 400: PayrollPeriodUpdateResponseSerializer, 403: PayrollPeriodUpdateResponseSerializer},
        description="Partially update a payroll period."
    )
    @transaction.atomic
    def patch(self, request, period_id):
        return self._update(request, period_id, partial=True)

    def _update(self, request, period_id, partial):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        period = self.get_object(period_id)
        if not period:
            return Response({
                "status": False,
                "message": "Payroll period not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = PayrollPeriodUpdateSerializer(period, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PayrollPeriodDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Payroll period updated.",
                "data": {"period": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        responses={200: PayrollPeriodDeleteResponseSerializer, 403: PayrollPeriodDeleteResponseSerializer, 404: PayrollPeriodDeleteResponseSerializer},
        description="Delete a payroll period."
    )
    @transaction.atomic
    def delete(self, request, period_id):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        period = self.get_object(period_id)
        if not period:
            return Response({
                "status": False,
                "message": "Payroll period not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = PayrollPeriodService.delete_payroll_period(period)
        if success:
            return Response({
                "status": True,
                "message": "Payroll period deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete payroll period.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PayrollPeriodCloseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        responses={200: PayrollPeriodUpdateResponseSerializer, 403: PayrollPeriodUpdateResponseSerializer, 404: PayrollPeriodUpdateResponseSerializer},
        description="Close a payroll period (prevent further modifications)."
    )
    @transaction.atomic
    def post(self, request, period_id):
        if not can_manage_payroll(request.user):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        period = PayrollPeriodService.get_payroll_period_by_id(period_id)
        if not period:
            return Response({
                "status": False,
                "message": "Payroll period not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if period.is_closed:
            return Response({
                "status": False,
                "message": "Period already closed.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        updated = PayrollPeriodService.close_period(period)
        data = PayrollPeriodDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Payroll period closed.",
            "data": {"period": data}
        })


class CurrentPayrollPeriodView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["HR - Payroll (Periods)"],
        responses={200: PayrollPeriodDetailResponseSerializer, 404: PayrollPeriodDetailResponseSerializer},
        description="Get the current active payroll period (based on today's date)."
    )
    def get(self, request):
        period = PayrollPeriodService.get_current_payroll_period()
        if not period:
            return Response({
                "status": False,
                "message": "No current payroll period found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = PayrollPeriodDisplaySerializer(period, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Current payroll period retrieved.",
            "data": {"period": data}
        })