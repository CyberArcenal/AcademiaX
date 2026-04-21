import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from users.models import User
from users.serializers.user import (
    UserMinimalSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserDisplaySerializer,
)
from users.services.user import UserService

logger = logging.getLogger(__name__)

def can_manage_user(user):
    return user.is_authenticated and (user.is_staff or user.role == 'ADMIN')

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class UserCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()

class UserCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UserCreateResponseData(allow_null=True)

class UserUpdateResponseData(serializers.Serializer):
    user = UserDisplaySerializer()

class UserUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UserUpdateResponseData(allow_null=True)

class UserDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class UserDetailResponseData(serializers.Serializer):
    user = UserDisplaySerializer()

class UserDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UserDetailResponseData(allow_null=True)

class UserListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = UserMinimalSerializer(many=True)

class UserListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UserListResponseData()

class UserMeResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = UserDisplaySerializer(allow_null=True)

class UserChangePasswordRequestSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

class UserChangePasswordResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

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

class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="role", type=str, description="Filter by role", required=False),
            OpenApiParameter(name="active_only", type=bool, required=False),
        ],
        responses={200: UserListResponseSerializer},
        description="List users (admin only)."
    )
    def get(self, request):
        if not can_manage_user(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        role = request.query_params.get("role")
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        queryset = User.objects.all()
        if role:
            queryset = queryset.filter(role=role)
        if active_only:
            queryset = queryset.filter(is_active=True)
        queryset = queryset.order_by('-date_joined')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        data = wrap_paginated_data(paginator, page, request, UserMinimalSerializer)
        return Response({
            "status": True,
            "message": "Users retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Users"],
        request=UserCreateSerializer,
        responses={201: UserCreateResponseSerializer, 400: UserCreateResponseSerializer, 403: UserCreateResponseSerializer},
        description="Create a new user (admin only)."
    )
    @transaction.atomic
    def post(self, request):
        if not can_manage_user(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "status": True,
                "message": "User created.",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @extend_schema(
        tags=["Users"],
        responses={200: UserDetailResponseSerializer, 404: UserDetailResponseSerializer, 403: UserDetailResponseSerializer},
        description="Retrieve a single user by ID (admin or self)."
    )
    def get(self, request, user_id):
        if not (request.user.id == user_id or request.user.is_staff):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object(user_id)
        if not user:
            return Response({
                "status": False,
                "message": "User not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        data = UserDisplaySerializer(user, context={"request": request}).data
        return Response({
            "status": True,
            "message": "User retrieved.",
            "data": {"user": data}
        })

    @extend_schema(
        tags=["Users"],
        request=UserUpdateSerializer,
        responses={200: UserUpdateResponseSerializer, 400: UserUpdateResponseSerializer, 403: UserUpdateResponseSerializer},
        description="Update a user (admin or self)."
    )
    @transaction.atomic
    def put(self, request, user_id):
        return self._update(request, user_id, partial=False)

    @extend_schema(
        tags=["Users"],
        request=UserUpdateSerializer,
        responses={200: UserUpdateResponseSerializer, 400: UserUpdateResponseSerializer, 403: UserUpdateResponseSerializer},
        description="Partially update a user."
    )
    @transaction.atomic
    def patch(self, request, user_id):
        return self._update(request, user_id, partial=True)

    def _update(self, request, user_id, partial):
        if not (request.user.id == user_id or request.user.is_staff):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object(user_id)
        if not user:
            return Response({
                "status": False,
                "message": "User not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Prevent role change for non-admin
        if 'role' in request.data and not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Only admin can change role.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = UserUpdateSerializer(user, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = UserDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "User updated.",
                "data": {"user": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Users"],
        responses={200: UserDeleteResponseSerializer, 403: UserDeleteResponseSerializer, 404: UserDeleteResponseSerializer},
        description="Delete a user (soft delete, admin only)."
    )
    @transaction.atomic
    def delete(self, request, user_id):
        if not request.user.is_staff:
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object(user_id)
        if not user:
            return Response({
                "status": False,
                "message": "User not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if user == request.user:
            return Response({
                "status": False,
                "message": "Cannot delete your own account.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        success = UserService.delete_user(user)
        if success:
            return Response({
                "status": True,
                "message": "User deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete user.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        parameters=[
            OpenApiParameter(name="query", type=str, description="Search term", required=True),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: UserListResponseSerializer},
        description="Search users by username, email, or name (admin only)."
    )
    def get(self, request):
        if not can_manage_user(request.user):
            return Response({
                "status": False,
                "message": "Admin permission required.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        query = request.query_params.get("query")
        if not query:
            return Response({
                "status": False,
                "message": "Query parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        users = UserService.search_users(query)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(users, request)
        data = wrap_paginated_data(paginator, page, request, UserMinimalSerializer)
        return Response({
            "status": True,
            "message": "Search results.",
            "data": data
        })


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        responses={200: UserMeResponseSerializer},
        description="Get current authenticated user's profile."
    )
    def get(self, request):
        data = UserDisplaySerializer(request.user, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Current user retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Users"],
        request=UserUpdateSerializer,
        responses={200: UserUpdateResponseSerializer, 400: UserUpdateResponseSerializer},
        description="Update current user's profile."
    )
    @transaction.atomic
    def put(self, request):
        return self._update(request, partial=False)

    @extend_schema(
        tags=["Users"],
        request=UserUpdateSerializer,
        responses={200: UserUpdateResponseSerializer, 400: UserUpdateResponseSerializer},
        description="Partially update current user's profile."
    )
    @transaction.atomic
    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial):
        user = request.user
        # Prevent role change via this endpoint
        if 'role' in request.data:
            return Response({
                "status": False,
                "message": "Cannot change role via this endpoint.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserUpdateSerializer(user, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = UserDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Profile updated.",
                "data": {"user": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        request=UserChangePasswordRequestSerializer,
        responses={200: UserChangePasswordResponseSerializer, 400: UserChangePasswordResponseSerializer},
        description="Change current user's password."
    )
    @transaction.atomic
    def post(self, request):
        serializer = UserChangePasswordRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                "status": False,
                "message": "Old password is incorrect.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({
            "status": True,
            "message": "Password changed successfully.",
            "data": None
        })