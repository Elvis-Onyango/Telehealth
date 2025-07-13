from django.urls import path
from .views import MessageListView, SendMessageView,ChatTemplateView

urlpatterns = [
    path('messages/<int:contact_id>/', MessageListView.as_view(), name='message-thread'),
    path('messages/send/', SendMessageView.as_view(), name='send-message'),
    path('room/', ChatTemplateView.as_view(), name='chat-room'),
    
  

]
