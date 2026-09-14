from django.contrib import admin

from .models import *


class ChatRoomMemberInline(admin.TabularInline):
    model = ChatRoomMember
    extra = 1
    autocomplete_fields = ["user"]


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ["__str__", "course", "created_by", "created_at"]
    list_filter = ["course"]
    search_fields = ["name", "course__name"]
    autocomplete_fields = ["course", "created_by"]
    inlines = [ChatRoomMemberInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["room", "sender", "content", "sent_at"]
    list_filter = ["room"]
    search_fields = ["sender__email", "content"]
    autocomplete_fields = ["room", "sender"]