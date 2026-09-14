from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ChatMessageViewSet, ChatRoomMemberViewSet, ChatRoomViewSet

router = DefaultRouter()
router.register("", ChatRoomViewSet, basename="chatroom")

urlpatterns = router.urls + [
    path(
        "<int:room_pk>/messages/",
        ChatMessageViewSet.as_view({"get": "list", "post": "create"}),
        name="chatroom-messages-list",
    ),
    path(
        "<int:room_pk>/members/",
        ChatRoomMemberViewSet.as_view({"get": "list"}),
        name="chatroom-members-list",
    ),
]