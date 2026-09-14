from rest_framework import serializers

from apps.feed.models import Feed, FeedComment, Notification


class FeedCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = FeedComment
        fields = ["id", "feed", "author", "author_name", "content", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class FeedSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    comments = FeedCommentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Feed
        fields = ["id", "author", "author_name", "content", "created_at", "comments", "comment_count"]
        read_only_fields = ["id", "author", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "type", "message", "course", "chat_room", "is_read", "created_at", "url"]
        read_only_fields = ["id", "type", "message", "course", "chat_room", "created_at", "url"]