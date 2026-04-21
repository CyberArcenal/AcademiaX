import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from communication.models import Message
from communication.serializers.message import (
    MessageMinimalSerializer,
    MessageCreateSerializer,
    MessageUpdateSerializer,
    MessageDisplaySerializer,
)
from communication.services.message import MessageService
from communication.services.conversation import ConversationService

logger = logging.getLogger(__name__)

def can_view_conversation(user, conversation):
    if user.is_staff:
        return True
    return user in conversation.participants.all()

def can_edit_message(user, message):
    if user.is_staff:
        return True
    return message.sender == user

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class MessageCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    conversation = serializers.IntegerField()
    content = serializers.CharField()

class MessageCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MessageCreateResponseData(allow_null=True)

class MessageUpdateResponseData(serializers.Serializer):
    message = MessageDisplaySerializer()

class MessageUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MessageUpdateResponseData(allow_null=True)

class MessageDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class MessageDetailResponseData(serializers.Serializer):
    message = MessageDisplaySerializer()

class MessageDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MessageDetailResponseData(allow_null=True)

class MessageListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = MessageMinimalSerializer(many=True)

class MessageListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MessageListResponseData()

class MessageMarkDeliveredResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MessageDetailResponseData()

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

class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Messages"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="conversation_id", type=int, description="Conversation ID", required=True),
            OpenApiParameter(name="before_id", type=int, description="Get messages before this ID (for pagination)", required=False),
        ],
        responses={200: MessageListResponseSerializer},
        description="List messages in a conversation (must be participant)."
    )
    def get(self, request):
        conversation_id = request.query_params.get("conversation_id")
        if not conversation_id:
            return Response({
                "status": False,
                "message": "conversation_id parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        conversation = ConversationService.get_conversation_by_id(conversation_id)
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

        before_id = request.query_params.get("before_id")
        messages = MessageService.get_conversation_messages(conversation_id, before_id=before_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(messages, request)
        data = wrap_paginated_data(paginator, page, request, MessageMinimalSerializer)
        return Response({
            "status": True,
            "message": "Messages retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Communication - Messages"],
        request=MessageCreateSerializer,
        responses={201: MessageCreateResponseSerializer, 400: MessageCreateResponseSerializer, 403: MessageCreateResponseSerializer},
        description="Send a new message in a conversation."
    )
    @transaction.atomic
    def post(self, request):
        serializer = MessageCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            return Response({
                "status": True,
                "message": "Message sent.",
                "data": {
                    "id": message.id,
                    "conversation": message.conversation.id,
                    "content": message.content,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, message_id):
        try:
            return Message.objects.select_related('conversation', 'sender').get(id=message_id)
        except Message.DoesNotExist:
            return None

    @extend_schema(
        tags=["Communication - Messages"],
        responses={200: MessageDetailResponseSerializer, 404: MessageDetailResponseSerializer, 403: MessageDetailResponseSerializer},
        description="Retrieve a single message by ID (must have conversation access)."
    )
    def get(self, request, message_id):
        message = self.get_object(message_id)
        if not message:
            return Response({
                "status": False,
                "message": "Message not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_conversation(request.user, message.conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = MessageDisplaySerializer(message, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Message retrieved.",
            "data": {"message": data}
        })

    @extend_schema(
        tags=["Communication - Messages"],
        request=MessageUpdateSerializer,
        responses={200: MessageUpdateResponseSerializer, 400: MessageUpdateResponseSerializer, 403: MessageUpdateResponseSerializer},
        description="Edit a message (sender only, before it's read)."
    )
    @transaction.atomic
    def put(self, request, message_id):
        return self._update(request, message_id, partial=False)

    @extend_schema(
        tags=["Communication - Messages"],
        request=MessageUpdateSerializer,
        responses={200: MessageUpdateResponseSerializer, 400: MessageUpdateResponseSerializer, 403: MessageUpdateResponseSerializer},
        description="Partially edit a message."
    )
    @transaction.atomic
    def patch(self, request, message_id):
        return self._update(request, message_id, partial=True)

    def _update(self, request, message_id, partial):
        message = self.get_object(message_id)
        if not message:
            return Response({
                "status": False,
                "message": "Message not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_edit_message(request.user, message):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = MessageUpdateSerializer(message, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = MessageDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Message updated.",
                "data": {"message": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Communication - Messages"],
        responses={200: MessageDeleteResponseSerializer, 403: MessageDeleteResponseSerializer, 404: MessageDeleteResponseSerializer},
        description="Delete a message (soft delete for sender, hard delete for all if staff/sender)."
    )
    @transaction.atomic
    def delete(self, request, message_id):
        message = self.get_object(message_id)
        if not message:
            return Response({
                "status": False,
                "message": "Message not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_edit_message(request.user, message):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        # For simplicity: if staff, delete for all; else delete for sender
        if request.user.is_staff:
            success = MessageService.delete_for_all(message)
        else:
            success = MessageService.delete_for_sender(message)
        if success:
            return Response({
                "status": True,
                "message": "Message deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete message.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageMarkDeliveredView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Messages"],
        responses={200: MessageMarkDeliveredResponseSerializer, 403: MessageMarkDeliveredResponseSerializer, 404: MessageMarkDeliveredResponseSerializer},
        description="Mark a message as delivered (for receiving client)."
    )
    @transaction.atomic
    def post(self, request, message_id):
        message = MessageService.get_message_by_id(message_id)
        if not message:
            return Response({
                "status": False,
                "message": "Message not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_conversation(request.user, message.conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        updated = MessageService.mark_as_delivered(message)
        data = MessageDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Message marked as delivered.",
            "data": {"message": data}
        })


class MessageMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Messages"],
        responses={200: MessageMarkDeliveredResponseSerializer, 403: MessageMarkDeliveredResponseSerializer, 404: MessageMarkDeliveredResponseSerializer},
        description="Mark a message as read (for receiving client)."
    )
    @transaction.atomic
    def post(self, request, message_id):
        message = MessageService.get_message_by_id(message_id)
        if not message:
            return Response({
                "status": False,
                "message": "Message not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_conversation(request.user, message.conversation):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        updated = MessageService.mark_as_read(message)
        data = MessageDisplaySerializer(updated, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Message marked as read.",
            "data": {"message": data}
        })