import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from communication.models import Conversation
from communication.serializers.conversation import (
    ConversationMinimalSerializer,
    ConversationCreateSerializer,
    ConversationUpdateSerializer,
    ConversationDisplaySerializer,
)
from communication.services.conversation import ConversationService

logger = logging.getLogger(__name__)

def can_view_conversation(user, conversation):
    if user.is_staff:
        return True
    return user in conversation.participants.all()

def can_manage_conversation(user, conversation):
    # Creator or staff can update/delete
    if user.is_staff:
        return True
    return conversation.created_by == user

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class ConversationCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(allow_null=True)
    conversation_type = serializers.CharField()

class ConversationCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ConversationCreateResponseData(allow_null=True)

class ConversationUpdateResponseData(serializers.Serializer):
    conversation = ConversationDisplaySerializer()

class ConversationUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ConversationUpdateResponseData(allow_null=True)

class ConversationDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class ConversationDetailResponseData(serializers.Serializer):
    conversation = ConversationDisplaySerializer()

class ConversationDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ConversationDetailResponseData(allow_null=True)

class ConversationListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ConversationMinimalSerializer(many=True)

class ConversationListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = ConversationListResponseData()

class AddParticipantRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

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

class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Conversations"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
        ],
        responses={200: ConversationListResponseSerializer},
        description="List conversations the authenticated user participates in."
    )
    def get(self, request):
        user = request.user
        conversations = ConversationService.get_user_conversations(user.id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(conversations, request)
        data = wrap_paginated_data(paginator, page, request, ConversationMinimalSerializer)
        return Response({
            "status": True,
            "message": "Conversations retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Communication - Conversations"],
        request=ConversationCreateSerializer,
        responses={201: ConversationCreateResponseSerializer, 400: ConversationCreateResponseSerializer},
        description="Create a new conversation (private or group)."
    )
    @transaction.atomic
    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            conversation = serializer.save()
            return Response({
                "status": True,
                "message": "Conversation created.",
                "data": {
                    "id": conversation.id,
                    "name": conversation.name,
                    "conversation_type": conversation.conversation_type,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, conversation_id):
        return ConversationService.get_conversation_by_id(conversation_id)

    @extend_schema(
        tags=["Communication - Conversations"],
        responses={200: ConversationDetailResponseSerializer, 404: ConversationDetailResponseSerializer, 403: ConversationDetailResponseSerializer},
        description="Retrieve a single conversation by ID (must be participant)."
    )
    def get(self, request, conversation_id):
        conversation = self.get_object(conversation_id)
        if not conversation:
            return Response({
                "status": False,
                "message": "Conversation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_conversation(request.user, conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = ConversationDisplaySerializer(conversation, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Conversation retrieved.",
            "data": {"conversation": data}
        })

    @extend_schema(
        tags=["Communication - Conversations"],
        request=ConversationUpdateSerializer,
        responses={200: ConversationUpdateResponseSerializer, 400: ConversationUpdateResponseSerializer, 403: ConversationUpdateResponseSerializer},
        description="Update a conversation (name, add/remove participants)."
    )
    @transaction.atomic
    def put(self, request, conversation_id):
        return self._update(request, conversation_id, partial=False)

    @extend_schema(
        tags=["Communication - Conversations"],
        request=ConversationUpdateSerializer,
        responses={200: ConversationUpdateResponseSerializer, 400: ConversationUpdateResponseSerializer, 403: ConversationUpdateResponseSerializer},
        description="Partially update a conversation."
    )
    @transaction.atomic
    def patch(self, request, conversation_id):
        return self._update(request, conversation_id, partial=True)

    def _update(self, request, conversation_id, partial):
        conversation = self.get_object(conversation_id)
        if not conversation:
            return Response({
                "status": False,
                "message": "Conversation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_conversation(request.user, conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ConversationUpdateSerializer(conversation, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = ConversationDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Conversation updated.",
                "data": {"conversation": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Communication - Conversations"],
        responses={200: ConversationDeleteResponseSerializer, 403: ConversationDeleteResponseSerializer, 404: ConversationDeleteResponseSerializer},
        description="Delete a conversation (soft delete by default)."
    )
    @transaction.atomic
    def delete(self, request, conversation_id):
        conversation = self.get_object(conversation_id)
        if not conversation:
            return Response({
                "status": False,
                "message": "Conversation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_conversation(request.user, conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = ConversationService.delete_conversation(conversation)
        if success:
            return Response({
                "status": True,
                "message": "Conversation deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete conversation.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationAddParticipantView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Conversations"],
        request=AddParticipantRequestSerializer,
        responses={200: ConversationDetailResponseSerializer, 400: ConversationDetailResponseSerializer, 403: ConversationDetailResponseSerializer},
        description="Add a participant to a group conversation (creator or admin only)."
    )
    @transaction.atomic
    def post(self, request, conversation_id):
        conversation = ConversationService.get_conversation_by_id(conversation_id)
        if not conversation:
            return Response({
                "status": False,
                "message": "Conversation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_conversation(request.user, conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AddParticipantRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        from users.models import User
        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])
        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": "User not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        updated = ConversationService.add_participant(conversation, user)
        data = ConversationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Participant added.",
            "data": {"conversation": data}
        })


class ConversationRemoveParticipantView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Conversations"],
        request=AddParticipantRequestSerializer,
        responses={200: ConversationDetailResponseSerializer, 400: ConversationDetailResponseSerializer, 403: ConversationDetailResponseSerializer},
        description="Remove a participant from a group conversation (creator or admin only)."
    )
    @transaction.atomic
    def post(self, request, conversation_id):
        conversation = ConversationService.get_conversation_by_id(conversation_id)
        if not conversation:
            return Response({
                "status": False,
                "message": "Conversation not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_conversation(request.user, conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = AddParticipantRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Invalid data.",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        from users.models import User
        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])
        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": "User not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        if user == conversation.created_by:
            return Response({
                "status": False,
                "message": "Cannot remove the conversation creator.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        updated = ConversationService.remove_participant(conversation, user)
        data = ConversationDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Participant removed.",
            "data": {"conversation": data}
        })