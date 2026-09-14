import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import *


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        is_member = await self.is_room_member()
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content", "").strip()
        if not content:
            return

        message = await self.save_message(content)
        await self.notify_other_members()

        local_sent_at = timezone.localtime(message.sent_at)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": message.id,
                "content": message.content,
                "attachment_url": None,
                "attachment_name": None,
                "sender_id": self.user.id,
                "sender_name": self.user.get_full_name(),
                "sent_at": local_sent_at.strftime("%b %d, %Y %I:%M %p"),
            },
        )

    async def chat_message(self, event):
        """Handler name must match the 'type' key sent in group_send."""
        await self.send(text_data=json.dumps({
            "message_id": event["message_id"],
            "content": event.get("content"),
            "attachment_url": event.get("attachment_url"),
            "attachment_name": event.get("attachment_name"),
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "sent_at": event["sent_at"],
        }))

    @database_sync_to_async
    def is_room_member(self):
        return ChatRoomMember.objects.filter(room_id=self.room_id, user=self.user).exists()

    @database_sync_to_async
    def save_message(self, content):
        room = ChatRoom.objects.get(pk=self.room_id)
        return ChatMessage.objects.create(room=room, sender=self.user, content=content)

    @database_sync_to_async
    def notify_other_members(self):
        from apps.feed.models import Notification, NotificationType

        room = ChatRoom.objects.select_related("course").get(pk=self.room_id)
        room_name = room.name or room.course.name

        other_member_ids = ChatRoomMember.objects.filter(
            room_id=self.room_id
        ).exclude(user=self.user).values_list("user_id", flat=True)

        already_notified_ids = Notification.objects.filter(
            chat_room_id=self.room_id,
            recipient_id__in=other_member_ids,
            is_read=False,
        ).values_list("recipient_id", flat=True)

        ids_to_notify = set(other_member_ids) - set(already_notified_ids)

        Notification.objects.bulk_create([
            Notification(
                recipient_id=member_id,
                type=NotificationType.CHAT,
                message=f"You received new messages in {room_name}.",
                chat_room=room,
            )
            for member_id in ids_to_notify
        ])