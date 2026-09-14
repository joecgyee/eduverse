from rest_framework import serializers

from apps.chat.models import ChatMessage, ChatRoom, ChatRoomMember


class ChatRoomMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = ChatRoomMember
        fields = ["id", "room", "user", "user_name", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "room", "sender", "sender_name", "content", "attachment", "sent_at"]
        read_only_fields = ["id", "sender", "sent_at"]


class ChatRoomSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    member_count = serializers.IntegerField(source="members.count", read_only=True)

    class Meta:
        model = ChatRoom
        fields = [
            "id", "course", "course_name", "course_code", "name",
            "created_by", "created_at", "member_count",
        ]
        read_only_fields = ["id", "created_by", "created_at"]