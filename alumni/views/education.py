import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from alumni.models import PostGraduateEducation
from alumni.serializers.education import (
    PostGraduateEducationMinimalSerializer,
    PostGraduateEducationCreateSerializer,
    PostGraduateEducationUpdateSerializer,
    PostGraduateEducationDisplaySerializer,
)
from alumni.services.education import PostGraduateEducationService
from common.base.paginations import StandardResultsSetPagination

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class EducationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    alumni = serializers.IntegerField()
    degree = serializers.CharField()
    institution = serializers.CharField()

class EducationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EducationCreateResponseData(allow_null=True)

class EducationUpdateResponseData(serializers.Serializer):
    education = PostGraduateEducationDisplaySerializer()

class EducationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EducationUpdateResponseData(allow_null=True)

class EducationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class EducationDetailResponseData(serializers.Serializer):
    education = PostGraduateEducationDisplaySerializer()

class EducationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EducationDetailResponseData(allow_null=True)

class EducationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PostGraduateEducationMinimalSerializer(many=True)

class EducationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = EducationListResponseData()

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

class EducationListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Alumni - Education"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="alumni_id", type=int, description="Filter by alumni ID", required=False),
        ],
        responses={200: EducationListResponseSerializer},
        description="List postgraduate education records, optionally filtered by alumni."
    )
    def get(self, request):
        alumni_id = request.query_params.get("alumni_id")
        if alumni_id:
            educations = PostGraduateEducationService.get_educations_by_alumni(alumni_id)
        else:
            educations = PostGraduateEducation.objects.all().select_related('alumni').order_by('-year_end')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(educations, request)
        data = wrap_paginated_data(paginator, page, request, PostGraduateEducationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Education records retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Alumni - Education"],
        request=PostGraduateEducationCreateSerializer,
        responses={201: EducationCreateResponseSerializer, 400: EducationCreateResponseSerializer},
        description="Create a new postgraduate education record."
    )
    @transaction.atomic
    def post(self, request):
        serializer = PostGraduateEducationCreateSerializer(data=request.data)
        if serializer.is_valid():
            education = serializer.save()
            return Response({
                "status": True,
                "message": "Education record created.",
                "data": {
                    "id": education.id,
                    "alumni": education.alumni.id,
                    "degree": education.degree,
                    "institution": education.institution,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class EducationDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, education_id):
        return PostGraduateEducationService.get_education_by_id(education_id)

    @extend_schema(
        tags=["Alumni - Education"],
        responses={200: EducationDetailResponseSerializer, 404: EducationDetailResponseSerializer},
        description="Retrieve a single education record by ID."
    )
    def get(self, request, education_id):
        education = self.get_object(education_id)
        if not education:
            return Response({
                "status": False,
                "message": "Education record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = PostGraduateEducationDisplaySerializer(education, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Education record retrieved.",
            "data": {"education": data}
        })

    @extend_schema(
        tags=["Alumni - Education"],
        request=PostGraduateEducationUpdateSerializer,
        responses={200: EducationUpdateResponseSerializer, 400: EducationUpdateResponseSerializer, 403: EducationUpdateResponseSerializer},
        description="Update an education record."
    )
    @transaction.atomic
    def put(self, request, education_id):
        return self._update(request, education_id, partial=False)

    @extend_schema(
        tags=["Alumni - Education"],
        request=PostGraduateEducationUpdateSerializer,
        responses={200: EducationUpdateResponseSerializer, 400: EducationUpdateResponseSerializer, 403: EducationUpdateResponseSerializer},
        description="Partially update an education record."
    )
    @transaction.atomic
    def patch(self, request, education_id):
        return self._update(request, education_id, partial=True)

    def _update(self, request, education_id, partial):
        education = self.get_object(education_id)
        if not education:
            return Response({
                "status": False,
                "message": "Education record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated:
            return Response({
                "status": False,
                "message": "Authentication required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        if not (user.is_staff or (education.alumni.user and user == education.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = PostGraduateEducationUpdateSerializer(education, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = PostGraduateEducationDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Education record updated.",
                "data": {"education": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Alumni - Education"],
        responses={200: EducationDeleteResponseSerializer, 403: EducationDeleteResponseSerializer, 404: EducationDeleteResponseSerializer},
        description="Delete an education record (hard delete)."
    )
    @transaction.atomic
    def delete(self, request, education_id):
        education = self.get_object(education_id)
        if not education:
            return Response({
                "status": False,
                "message": "Education record not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not user.is_authenticated or not (user.is_staff or (education.alumni.user and user == education.alumni.user)):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = PostGraduateEducationService.delete_education(education)
        if success:
            return Response({
                "status": True,
                "message": "Education record deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete education record.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)