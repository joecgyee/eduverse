from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.chat.models import ChatMessage, ChatRoom, ChatRoomMember

from .serializers import ChatMessageSerializer, ChatRoomMemberSerializer, ChatRoomSerializer

CHATROOM_TAGS = ["Chat Rooms"]


@extend_schema_view(
    list=extend_schema(
        summary="List your chat rooms",
        description="Returns chat rooms where the authenticated user is a member.",
        tags=CHATROOM_TAGS,
    ),
    retrieve=extend_schema(summary="Get a single chat room's details", tags=CHATROOM_TAGS),
)
class ChatRoomViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Read-only via API — room creation stays on the website's own flows
    (auto-created per course, or student-started via chat:start), since
    membership logic there is more involved than a plain create.
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.filter(members__user=self.request.user).select_related("course")


@extend_schema_view(
    list=extend_schema(
        summary="List messages in a room",
        description="Returns message history for the room, oldest first. You must be a member of the room.",
        tags=CHATROOM_TAGS,
    ),
    create=extend_schema(
        summary="Post a message via REST",
        description="Saves a message to the room. Note: this does not broadcast live over the "
                    "websocket to other connected clients — live delivery happens via the chat "
                    "consumer. Use this mainly to fetch/append history programmatically.",
        tags=CHATROOM_TAGS,
    ),
)
class ChatMessageViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_pk = self.kwargs["room_pk"]
        is_member = ChatRoomMember.objects.filter(room_id=room_pk, user=self.request.user).exists()
        if not is_member:
            raise PermissionDenied("You are not a member of this chat room.")
        return ChatMessage.objects.filter(room_id=room_pk).select_related("sender").order_by("sent_at")

    def perform_create(self, serializer):
        room_pk = self.kwargs["room_pk"]
        is_member = ChatRoomMember.objects.filter(room_id=room_pk, user=self.request.user).exists()
        if not is_member:
            raise PermissionDenied("You are not a member of this chat room.")
        serializer.save(sender=self.request.user, room_id=room_pk)


@extend_schema_view(
    list=extend_schema(
        summary="List members of a room",
        description="Returns all users who are members of the given chat room.",
        tags=CHATROOM_TAGS,
    ),
)
class ChatRoomMemberViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ChatRoomMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoomMember.objects.filter(room_id=self.kwargs["room_pk"]).select_related("user")