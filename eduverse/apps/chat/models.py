from django.conf import settings
from django.db import models

from apps.courses.models import Course


class ChatRoom(models.Model):
    """A real-time chat session, scoped to a course."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="chat_rooms"
    )
    name = models.CharField(max_length=200, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_rooms_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_rooms"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or f"ChatRoom<{self.course.name}>"


class ChatRoomMember(models.Model):
    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_room_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_room_members"
        constraints = [
            models.UniqueConstraint(
                fields=["room", "user"], name="unique_room_member"
            )
        ]

    def __str__(self):
        return f"{self.user.email} in {self.room}"


class ChatMessage(models.Model):
    """Persisted messages sent through the websocket chat consumer."""

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages_sent",
    )
    content = models.CharField(max_length=2000, null=True, blank=True)
    attachment = models.FileField(
        upload_to="chat_attachments/%Y/%m/", null=True, blank=True
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        indexes = [
            models.Index(fields=["room", "sent_at"]),
        ]
        ordering = ["sent_at"]

    def __str__(self):
        return f"Message<{self.sender.email} @ {self.sent_at}>"