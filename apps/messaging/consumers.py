import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken
from .models import Conversation, Message
from apps.users.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'

        # Authenticate via JWT
        query_string = parse_qs(self.scope.get('query_string').decode())
        token_list = query_string.get('token', [])

        if not token_list:
            await self.close()
            return
        
        try:
            access_token = AccessToken(token_list[0])
            user_id = access_token['user_id']
            self.user = await self.get_user(user_id)
        except Exception:
            await self.close()
            return

        # Join conversation group
        await self.channel_layer.group_add(self.conversation_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.conversation_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            content = data['content']
            file = data.get('file')
            file_type = data.get('file_type')

            message = await self.create_message(content, file, file_type)
            if message:
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {'type': 'chat_message', 'message': await self.message_to_json(message)}
                )

        elif message_type == 'read_messages':
            await self.mark_messages_as_read()

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def message_to_json(self, message):
        file_url = self.scope.get('scheme', 'https') + '://' + self.scope['server'][0] + (':' + str(self.scope['server'][1]) if self.scope['server'][1] != 80 else '') + message.file.url if message.file else None

        return {
            'id': message.id,
            'sender': message.sender.id,
            'sender_name': message.sender.get_full_name(),
            'is_doctor': message.sender.role == 'doctor',
            'content': message.content,
            'file': file_url,
            'file_type': message.file_type,
            'timestamp': str(message.timestamp),
            'read': message.read
        }

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.filter(id=user_id).first() or AnonymousUser()

    @database_sync_to_async
    def create_message(self, content, file=None, file_type=None):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            if self.user not in [conversation.doctor.user, conversation.patient.user]:
                return None

            return Message.objects.create(conversation=conversation, sender=self.user, content=content, file=file, file_type=file_type)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_messages_as_read(self):
        Message.objects.filter(conversation_id=self.conversation_id, read=False).update(read=True)
