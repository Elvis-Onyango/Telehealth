from django.urls import path
from .views import (
    ChatTemplateView,
    MessageAttachmentView,
    MessageContactsView,
    MessageListView,
    SendMessageView,
)

urlpatterns = [
    path("contacts/", MessageContactsView.as_view(), name="message-contacts"),
    path("messages/<int:contact_id>/", MessageListView.as_view(), name="message-thread"),
    path("messages/<int:message_id>/attachment/", MessageAttachmentView.as_view(), name="message-attachment"),
    path("messages/send/", SendMessageView.as_view(), name="send-message"),
    path("room/", ChatTemplateView.as_view(), name="chat-room"),
]
