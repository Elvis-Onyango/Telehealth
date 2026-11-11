import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import User

from .access import can_message
from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        contact_id = self.scope["url_route"]["kwargs"]["contact_id"]
        subprotocols = self.scope.get("subprotocols", [])
        token = subprotocols[1] if len(subprotocols) == 2 and subprotocols[0] == "jwt" else None

        if not token:
            await self.close(code=4401)
            return

        try:
            access_token = AccessToken(token)
            self.user = await self.get_user(access_token["user_id"])
        except (TokenError, KeyError, TypeError, ValueError):
            await self.close(code=4401)
            return

        if self.user is None:
            await self.close(code=4401)
            return

        self.contact = await self.get_contact(contact_id)
        if self.contact is None or not await self.has_chat_access(self.user, self.contact):
            await self.close(code=4403)
            return

        first_id, second_id = sorted((self.user.pk, self.contact.pk))
        self.group_name = f"chat_{first_id}_{second_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept(subprotocol="jwt")

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            await self.send_json({"type": "error", "detail": "Text messages are required."})
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "detail": "Invalid JSON."})
            return

        if not isinstance(data, dict):
            await self.send_json({"type": "error", "detail": "Invalid message."})
            return

        if data.get("type") == "chat_message":
            content = data.get("content")
            if not isinstance(content, str) or not content.strip():
                await self.send_json({"type": "error", "detail": "Message cannot be empty."})
                return
            if len(content) > 5000:
                await self.send_json({"type": "error", "detail": "Message exceeds 5000 characters."})
                return

            message = await self.create_message(content.strip())
            if message is None:
                await self.send_json({"type": "error", "detail": "Messaging access has been revoked."})
                return

            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.message", "message": message},
            )
        elif data.get("type") == "read_messages":
            message_ids = await self.mark_messages_as_read()
            if message_ids:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chat.read_receipt",
                        "reader_id": self.user.pk,
                        "message_ids": message_ids,
                    },
                )
        else:
            await self.send_json({"type": "error", "detail": "Unsupported event type."})

    async def chat_message(self, event):
        await self.send_json({"type": "chat_message", "message": event["message"]})

    async def chat_read_receipt(self, event):
        await self.send_json(
            {
                "type": "read_receipt",
                "reader_id": event["reader_id"],
                "message_ids": event["message_ids"],
            }
        )

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.filter(pk=user_id, is_active=True).first()

    @database_sync_to_async
    def get_contact(self, contact_id):
        return User.objects.filter(pk=contact_id, is_active=True).first()

    @database_sync_to_async
    def has_chat_access(self, user, contact):
        return can_message(user, contact)

    @database_sync_to_async
    def create_message(self, content):
        user = User.objects.filter(pk=self.user.pk, is_active=True).first()
        contact = User.objects.filter(pk=self.contact.pk, is_active=True).first()
        if user is None or contact is None or not can_message(user, contact):
            return None

        message = Message.objects.create(
            sender=user,
            recipient=contact,
            content=content,
            message_type="text",
        )
        return {
            "id": message.pk,
            "sender": user.pk,
            "sender_name": user.get_full_name() or user.username,
            "recipient": contact.pk,
            "content": message.content,
            "message_type": message.message_type,
            "timestamp": message.timestamp.isoformat(),
            "is_read": message.is_read,
        }

    @database_sync_to_async
    def mark_messages_as_read(self):
        user = User.objects.filter(pk=self.user.pk, is_active=True).first()
        contact = User.objects.filter(pk=self.contact.pk, is_active=True).first()
        if user is None or contact is None or not can_message(user, contact):
            return []

        unread_messages = Message.objects.filter(
            sender=contact,
            recipient=user,
            is_read=False,
        )
        message_ids = list(unread_messages.values_list("pk", flat=True))
        if message_ids:
            unread_messages.update(is_read=True)
        return message_ids

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
