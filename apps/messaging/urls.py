from django.urls import path
from . import views
app_name = "messaging"
urlpatterns = [
    path('chat/',views.ChatPage.as_view(), name = 'chat-page'),
    # Conversation endpoints
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/start/', views.StartConversationView.as_view(), name='start-conversation'),
    
    # Message endpoints
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('conversations/<int:conversation_id>/read/', views.MarkMessagesAsReadView.as_view(), name='mark-read'),
    
    # File upload endpoint
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
]