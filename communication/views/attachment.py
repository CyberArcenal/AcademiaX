import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers

from common.base.paginations import StandardResultsSetPagination
from communication.models import MessageAttachment, Message
from communication.serializers.attachment import (
    MessageAttachmentMinimalSerializer,
    MessageAttachmentCreateSerializer,
    MessageAttachmentUpdateSerializer,
    MessageAttachmentDisplaySerializer,
)
from communication.services.attachment import MessageAttachmentService
from communication.services.message import MessageService

logger = logging.getLogger(__name__)

def can_view_message_attachment(user, attachment):
    if user.is_staff:
        return True
    # Check if user is participant in the conversation of the message
    return user in attachment.message.conversation.participants.all()

def can_manage_message_attachment(user, attachment):
    # Sender of the message or staff can manage attachments
    if user.is_staff:
        return True
    return attachment.message.sender == user

# ----------------------------------------------------------------------
# Response serializers
# ----------------------------------------------------------------------

class AttachmentCreateResponseData(serializers.Serializer):
    id = serializers.IntegerField()
    message = serializers.IntegerField()
    file_name = serializers.CharField()

class AttachmentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttachmentCreateResponseData(allow_null=True)

class AttachmentUpdateResponseData(serializers.Serializer):
    attachment = MessageAttachmentDisplaySerializer()

class AttachmentUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttachmentUpdateResponseData(allow_null=True)

class AttachmentDeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = None

class AttachmentDetailResponseData(serializers.Serializer):
    attachment = MessageAttachmentDisplaySerializer()

class AttachmentDetailResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttachmentDetailResponseData(allow_null=True)

class AttachmentListResponseData(serializers.Serializer):
    page = serializers.IntegerField()
    hasNext = serializers.BooleanField()
    hasPrev = serializers.BooleanField()
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = MessageAttachmentMinimalSerializer(many=True)

class AttachmentListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = AttachmentListResponseData()

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

class MessageAttachmentListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Communication - Attachments"],
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="message_id", type=int, description="Filter by message ID", required=True),
        ],
        responses={200: AttachmentListResponseSerializer},
        description="List attachments for a specific message (must have conversation access)."
    )
    def get(self, request):
        message_id = request.query_params.get("message_id")
        if not message_id:
            return Response({
                "status": False,
                "message": "message_id parameter required.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        message = MessageService.get_message_by_id(message_id)
        if not message:
            return Response({
                "status": False,
                "message": "Message not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        # Check conversation access
        if not (request.user.is_staff or request.user in message.conversation.participants.all()):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        attachments = MessageAttachmentService.get_attachments_by_message(message_id)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(attachments, request)
        data = wrap_paginated_data(paginator, page, request, MessageAttachmentMinimalSerializer)
        return Response({
            "status": True,
            "message": "Attachments retrieved.",
            "data": data
        })

    @extend_schema(
        tags=["Communication - Attachments"],
        request=MessageAttachmentCreateSerializer,
        responses={201: AttachmentCreateResponseSerializer, 400: AttachmentCreateResponseSerializer, 403: AttachmentCreateResponseSerializer},
        description="Upload an attachment to a message (sender or staff)."
    )
    @transaction.atomic
    def post(self, request):
        serializer = MessageAttachmentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attachment = serializer.save()
            return Response({
                "status": True,
                "message": "Attachment uploaded.",
                "data": {
                    "id": attachment.id,
                    "message": attachment.message.id,
                    "file_name": attachment.file_name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MessageAttachmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, attachment_id):
        try:
            return MessageAttachment.objects.select_related('message__conversation', 'uploaded_by').get(id=attachment_id)
        except MessageAttachment.DoesNotExist:
            return None

    @extend_schema(
        tags=["Communication - Attachments"],
        responses={200: AttachmentDetailResponseSerializer, 404: AttachmentDetailResponseSerializer, 403: AttachmentDetailResponseSerializer},
        description="Retrieve a single attachment by ID (must have conversation access)."
    )
    def get(self, request, attachment_id):
        attachment = self.get_object(attachment_id)
        if not attachment:
            return Response({
                "status": False,
                "message": "Attachment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_view_message_attachment(request.user, attachment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        data = MessageAttachmentDisplaySerializer(attachment, context={"request": request}).data
        return Response({
            "status": True,
            "message": "Attachment retrieved.",
            "data": {"attachment": data}
        })

    @extend_schema(
        tags=["Communication - Attachments"],
        request=MessageAttachmentUpdateSerializer,
        responses={200: AttachmentUpdateResponseSerializer, 400: AttachmentUpdateResponseSerializer, 403: AttachmentUpdateResponseSerializer},
        description="Update an attachment (only notes, usually not needed)."
    )
    @transaction.atomic
    def put(self, request, attachment_id):
        return self._update(request, attachment_id, partial=False)

    @extend_schema(
        tags=["Communication - Attachments"],
        request=MessageAttachmentUpdateSerializer,
        responses={200: AttachmentUpdateResponseSerializer, 400: AttachmentUpdateResponseSerializer, 403: AttachmentUpdateResponseSerializer},
        description="Partially update an attachment."
    )
    @transaction.atomic
    def patch(self, request, attachment_id):
        return self._update(request, attachment_id, partial=True)

    def _update(self, request, attachment_id, partial):
        attachment = self.get_object(attachment_id)
        if not attachment:
            return Response({
                "status": False,
                "message": "Attachment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_message_attachment(request.user, attachment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)
        # Only notes can be updated; other fields are read-only.
        serializer = MessageAttachmentUpdateSerializer(attachment, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = serializer.save()
            data = MessageAttachmentDisplaySerializer(updated, context={"request": request}).data
            return Response({
                "status": True,
                "message": "Attachment updated.",
                "data": {"attachment": data}
            })
        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Communication - Attachments"],
        responses={200: AttachmentDeleteResponseSerializer, 403: AttachmentDeleteResponseSerializer, 404: AttachmentDeleteResponseSerializer},
        description="Delete an attachment (sender or staff)."
    )
    @transaction.atomic
    def delete(self, request, attachment_id):
        attachment = self.get_object(attachment_id)
        if not attachment:
            return Response({
                "status": False,
                "message": "Attachment not found.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        if not can_manage_message_attachment(request.user, attachment):
            return Response({
                "status": False,
                "message": "Permission denied.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        success = MessageAttachmentService.delete_attachment(attachment)
        if success:
            return Response({
                "status": True,
                "message": "Attachment deleted.",
                "data": None
            })
        return Response({
            "status": False,
            "message": "Failed to delete attachment.",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)