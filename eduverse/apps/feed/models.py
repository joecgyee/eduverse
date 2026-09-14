from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    ENROLLMENT = "enrollment", "New Enrollment"
    COURSE_MATERIAL = "course_material", "New Course Material"
    CHAT = "chat", "New Chat"
    FEED_COMMENT = "feed_comment", "New Comment"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    message = models.CharField(max_length=255)
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    chat_room = models.ForeignKey(
        "chat.ChatRoom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification<{self.recipient.email}: {self.type}>"

    def get_absolute_url(self):
        from django.urls import reverse
        if self.course_id:
            return reverse("courses:detail", kwargs={"pk": self.course_id})
        if self.chat_room_id:
            return reverse("chat:room_detail", kwargs={"pk": self.chat_room_id})
        if self.type == NotificationType.FEED_COMMENT:
            return reverse("users:detail")
        return reverse("courses:list")
    

class Feed(models.Model):
    """Posted by users to their own feed page; visible to all users."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feed_posts"
    )
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feeds"
        indexes = [
            models.Index(fields=["author", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feed<{self.author.email}: {self.content[:30]}>"


class FeedComment(models.Model):
    """A comment left by any user under a Feed post."""

    feed = models.ForeignKey(
        Feed, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feed_comments",
    )
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feed_comments"
        indexes = [
            models.Index(fields=["feed", "created_at"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment<{self.author.email} on Feed #{self.feed_id}>"