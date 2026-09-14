from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.feed.models import Feed, FeedComment, Notification

from .serializers import FeedCommentSerializer, FeedSerializer, NotificationSerializer

FEED_TAGS = ["Feed"]
NOTIFICATION_TAGS = ["Notifications"]


@extend_schema_view(
    list=extend_schema(
        summary="List feed posts",
        description="Returns all posts, newest first. Filter with `?search=` (post content) "
                    "or `?author=<user id>`.",
        tags=FEED_TAGS,
        parameters=[
            OpenApiParameter(name="search", description="Search post content", required=False, type=str),
            OpenApiParameter(name="author", description="Filter by author's user ID", required=False, type=int),
        ],
    ),
    retrieve=extend_schema(summary="Get a single post, including its comments", tags=FEED_TAGS),
    create=extend_schema(
        summary="Create a post",
        description="Posts to your own feed as the authenticated user.",
        tags=FEED_TAGS,
    ),
    destroy=extend_schema(
        summary="Delete a post",
        description="You may only delete posts you authored.",
        tags=FEED_TAGS,
    ),
)
class FeedViewSet(viewsets.ModelViewSet):
    queryset = Feed.objects.select_related("author").prefetch_related("comments__author").all()
    serializer_class = FeedSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(content__icontains=search)
        author_id = self.request.query_params.get("author")
        if author_id:
            qs = qs.filter(author_id=author_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            raise PermissionDenied("You can only delete your own posts.")
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="List comments on a post",
        description="Returns all comments for the given feed post, oldest first.",
        tags=FEED_TAGS,
    ),
    create=extend_schema(
        summary="Comment on a post",
        description="Adds a comment as the authenticated user.",
        tags=FEED_TAGS,
    ),
    destroy=extend_schema(
        summary="Delete a comment",
        description="You may only delete comments you authored.",
        tags=FEED_TAGS,
    ),
)
class FeedCommentViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin,
                          mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FeedCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FeedComment.objects.filter(feed_id=self.kwargs["feed_pk"]).select_related("author")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, feed_id=self.kwargs["feed_pk"])

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            raise PermissionDenied("You can only delete your own comments.")
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="List your notifications",
        description="Returns notifications belonging to the authenticated user only.",
        tags=NOTIFICATION_TAGS,
    ),
    retrieve=extend_schema(summary="Get a single notification", tags=NOTIFICATION_TAGS),
    partial_update=extend_schema(
        summary="Mark a notification as read/unread",
        description="Typically used to set `is_read` to true after the user views it.",
        tags=NOTIFICATION_TAGS,
    ),
)
class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)