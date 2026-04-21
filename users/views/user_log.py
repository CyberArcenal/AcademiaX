import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from users.models.user_log import UserLog
from users.serializers.user_log import (
    UserLogMinimalSerializer,
    UserLogDisplaySerializer,
)

logger = logging.getLogger(__name__)

def can_view_user_logs(user):
    return user.is_authenticated and user.is_staff

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class UserLogListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = UserLogMinimalSerializer(many=True)

class UserLogListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UserLogListResponseData()

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

class UserLogListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users - Logs"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="user_id", type=int, description="Filter by user ID", required=False),
            OpenApiParameter(name="action", type=str, description="Filter by action", required=False),
        ],
        responses={200: UserLogListResponseSerializer},
        description="List user logs (admin only)."
    )
    def get(self, request):
        if not can_view_user_logs(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        user_id = request.query_params.get("user_id")
        action = request.query_params.get("action")
        queryset = UserLog.objects.all().select_related('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
        queryset = queryset.order_by('-created_at')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, UserLogMinimalSerializer)
        return Response({
            "status": True,
            "message": "User logs retrieved.",
            "data": data
        })