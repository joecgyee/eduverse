from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import FeedCommentViewSet, FeedViewSet, NotificationViewSet

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")
router.register("", FeedViewSet, basename="feed")

urlpatterns = router.urls + [
    path(
        "<int:feed_pk>/comments/",
        FeedCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="feed-comments-list",
    ),
    path(
        "<int:feed_pk>/comments/<int:pk>/",
        FeedCommentViewSet.as_view({"delete": "destroy"}),
        name="feed-comments-detail",
    ),
]