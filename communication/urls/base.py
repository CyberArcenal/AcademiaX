from django.urls import path
from communication.views.announcement import (
    AnnouncementListView,
    AnnouncementDetailView,
    AnnouncementPublishView,
)
from communication.views.notify_log import NotifyLogCRUD, NotifyLogResend, NotifyLogRetry

urlpatterns = [
    path("announcements/", AnnouncementListView.as_view(), name="announcement-list"),
    path("announcements/<int:announcement_id>/", AnnouncementDetailView.as_view(), name="announcement-detail"),
    path("announcements/<int:announcement_id>/publish/", AnnouncementPublishView.as_view(), name="announcement-publish"),
]

from communication.views.email_template import EmailTemplateCRUD
from communication.views.notification import (
    NotificationListView,
    NotificationDetailView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationUnreadCountView,
)

urlpatterns += [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<int:notification_id>/", NotificationDetailView.as_view(), name="notification-detail"),
    path("notifications/<int:notification_id>/mark-read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
    path("notifications/mark-all-read/", NotificationMarkAllReadView.as_view(), name="notification-mark-all-read"),
    path("notifications/unread-count/", NotificationUnreadCountView.as_view(), name="notification-unread-count"),
]

from communication.views.conversation import (
    ConversationListView,
    ConversationDetailView,
    ConversationAddParticipantView,
    ConversationRemoveParticipantView,
)

urlpatterns += [
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<int:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<int:conversation_id>/add-participant/", ConversationAddParticipantView.as_view(), name="conversation-add-participant"),
    path("conversations/<int:conversation_id>/remove-participant/", ConversationRemoveParticipantView.as_view(), name="conversation-remove-participant"),
]

from communication.views.message import (
    MessageListView,
    MessageDetailView,
    MessageMarkDeliveredView,
    MessageMarkReadView,
)

urlpatterns += [
    path("messages/", MessageListView.as_view(), name="message-list"),
    path("messages/<int:message_id>/", MessageDetailView.as_view(), name="message-detail"),
    path("messages/<int:message_id>/mark-delivered/", MessageMarkDeliveredView.as_view(), name="message-mark-delivered"),
    path("messages/<int:message_id>/mark-read/", MessageMarkReadView.as_view(), name="message-mark-read"),
]

from communication.views.attachment import (
    MessageAttachmentListView,
    MessageAttachmentDetailView,
)

urlpatterns += [
    path("attachments/", MessageAttachmentListView.as_view(), name="attachment-list"),
    path("attachments/<int:attachment_id>/", MessageAttachmentDetailView.as_view(), name="attachment-detail"),
]

from communication.views.broadcast_log import (
    BroadcastLogListView,
    BroadcastLogDetailView,
    BroadcastLogRetryView,
    BroadcastLogFailedView,
)

urlpatterns += [
    path("broadcast-logs/", BroadcastLogListView.as_view(), name="broadcast-log-list"),
    path("broadcast-logs/<int:log_id>/", BroadcastLogDetailView.as_view(), name="broadcast-log-detail"),
    path("broadcast-logs/<int:log_id>/retry/", BroadcastLogRetryView.as_view(), name="broadcast-log-retry"),
    path("broadcast-logs/failed/", BroadcastLogFailedView.as_view(), name="broadcast-log-failed"),
    
    
    
    # Email Templates
    path('email-templates/', EmailTemplateCRUD.as_view(), name='emailtemplate-list'),
    path('email-templates/<int:id>/', EmailTemplateCRUD.as_view(), name='emailtemplate-detail'),
    

    path("notifylogs/", NotifyLogCRUD.as_view(), name=""),
    path("notifylogs/<int:id>/", NotifyLogCRUD.as_view(), name=""),
    path("notifylogs/<int:id>/retry/", NotifyLogRetry.as_view(), name=""),
    path("notifylogs/<int:id>/resend/", NotifyLogResend.as_view(), name=""),
]