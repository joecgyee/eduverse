from django.contrib import admin

from .models import *


class FeedCommentInline(admin.TabularInline):
    model = FeedComment
    extra = 0
    autocomplete_fields = ["author"]
    readonly_fields = ["created_at"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "type", "message", "is_read", "created_at"]
    list_filter = ["type", "is_read"]
    search_fields = ["recipient__email", "message"]
    autocomplete_fields = ["recipient"]


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ["author", "content", "created_at"]
    search_fields = ["author__email", "content"]
    autocomplete_fields = ["author"]
    inlines = [FeedCommentInline]


@admin.register(FeedComment)
class FeedCommentAdmin(admin.ModelAdmin):
    list_display = ["author", "feed", "content", "created_at"]
    search_fields = ["author__email", "content"]
    autocomplete_fields = ["feed", "author"]