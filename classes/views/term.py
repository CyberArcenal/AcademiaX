import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from classes.models import Term
from classes.serializers.term import (
    TermMinimalSerializer,
    TermCreateSerializer,
    TermUpdateSerializer,
    TermDisplaySerializer,
)
from classes.services.term import TermService
from global_utils.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)

def can_manage_term(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class TermCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    academic_year = serializers.IntegerField()

class TermCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TermCreateResponseData(allow_null=True)

class TermUpdateResponseData(serializers.Serializer):
    term = TermDisplaySerializer()

class TermUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TermUpdateResponseData(allow_null=True)

class TermDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class TermDetailResponseData(serializers.Serializer):
    term = TermDisplaySerializer()

class TermDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TermDetailResponseData(allow_null=True)

class TermListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = TermMinimalSerializer(many=True)

class TermListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = TermListResponseData()

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

class TermListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Terms"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="academic_year_id", type=int, description="Filter by academic year ID", required=False),
            OpenApiParameter(name="active_only", type=bool, description="Only active terms", required=False),
        ],
        responses={200: TermListResponseSerializer},
        description="List terms, optionally filtered by academic year."
    )
    def get(self, request):
        academic_year_id = request.query_params.get("academic_year_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if academic_year_id:
            terms = TermService.get_terms_by_academic_year(academic_year_id, active_only=active_only)
        else:
            terms = Term.objects.all().select_related('academic_year')
            if active_only:
                terms = terms.filter(is_active=True)
            terms = terms.order_by('academic_year__start_date', 'term_number')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(terms, request)
        data = wrap_paginated_data(paginator, page, request, TermMinimalSerializer)
        return Response({
            "status": True,
            "message": "Terms retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Classes - Terms"],
        request=TermCreateSerializer,
        responses={201: TermCreateResponseSerializer, 400: TermCreateResponseSerializer, 403: TermCreateResponseSerializer},
        description="Create a new term (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_term(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = TermCreateSerializer(data=request.data)
        if serializer.is_valid():
            term = serializer.save()
            return Response({
                "status": True,
                "message": "Term created.",
                "data": {
                    "id": term.id,
                    "name": term.name,
                    "academic_year": term.academic_year.id,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TermDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, term_id):
        return TermService.get_term_by_id(term_id)

    @extend_schema(
        tags=["Classes - Terms"],
        responses={200: TermDetailResponseSerializer, 404: TermDetailResponseSerializer},
        description="Retrieve a single term by ID."
    )
    def get(self, request, term_id):
        term = self.get_object(term_id)
        if not term:
            return Response({
                "status": False,
                "message": "Term not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = TermDisplaySerializer(term, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Term retrieved.",
            "data": {"term": data}
        })

    @extend_schema(
        tags=["Classes - Terms"],
        request=TermUpdateSerializer,
        responses={200: TermUpdateResponseSerializer, 400: TermUpdateResponseSerializer, 403: TermUpdateResponseSerializer},
        description="Update a term (admin only)."
    )
    @transaction.atomic
    def put(self, request, term_id):
        return self._update(request, term_id, partial=False)

    @extend_schema(
        tags=["Classes - Terms"],
        request=TermUpdateSerializer,
        responses={200: TermUpdateResponseSerializer, 400: TermUpdateResponseSerializer, 403: TermUpdateResponseSerializer},
        description="Partially update a term."
    )
    @transaction.atomic
    def patch(self, request, term_id):
        return self._update(request, term_id, partial=True)

    def _update(self, request, term_id, partial):
        if not can_manage_term(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        term = self.get_object(term_id)
        if not term:
            return Response({
                "status": False,
                "message": "Term not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TermUpdateSerializer(term, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = TermDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Term updated.",
                "data": {"term": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Classes - Terms"],
        responses={200: TermDeleteResponseSerializer, 403: TermDeleteResponseSerializer, 404: TermDeleteResponseSerializer},
        description="Delete a term (admin only)."
    )
    @transaction.atomic
    def delete(self, request, term_id):
        if not can_manage_term(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        term = self.get_object(term_id)
        if not term:
            return Response({
                "status": False,
                "message": "Term not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        success = TermService.delete_term(term)
        if success:
            return Response({
                "status": True,
                "message": "Term deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete term.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TermActivateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Classes - Terms"],
        responses={200: TermDetailResponseSerializer, 403: TermDetailResponseSerializer, 404: TermDetailResponseSerializer},
        description="Activate a term (admin only)."
    )
    @transaction.atomic
    def post(self, request, term_id):
        if not can_manage_term(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        term = TermService.get_term_by_id(term_id)
        if not term:
            return Response({
                "status": False,
                "message": "Term not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = TermService.activate_term(term)
        data = TermDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Term activated.",
            "data": {"term": data}
        })


class TermDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Classes - Terms"],
        responses={200: TermDetailResponseSerializer, 403: TermDetailResponseSerializer, 404: TermDetailResponseSerializer},
        description="Deactivate a term (admin only)."
    )
    @transaction.atomic
    def post(self, request, term_id):
        if not can_manage_term(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        term = TermService.get_term_by_id(term_id)
        if not term:
            return Response({
                "status": False,
                "message": "Term not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        updated = TermService.deactivate_term(term)
        data = TermDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Term deactivated.",
            "data": {"term": data}
        })


class CurrentTermView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Classes - Terms"],
        parameters=[
            OpenApiParameter(name="academic_year_id", type=int, description="Academic year ID", required=False),
        ],
        responses={200: TermDetailResponseSerializer},
        description="Get the current active term (based on today's date)."
    )
    def get(self, request):
        academic_year_id = request.query_params.get("academic_year_id")
        term = TermService.get_current_term(academic_year_id)
        if not term:
            return Response({
                "status": False,
                "message": "No current term found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = TermDisplaySerializer(term, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Current term retrieved.",
            "data": {"term": data}
        })