from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import *
from .models import *

from django.db import models

@login_required
def notification_redirect_view(request, pk):
    """
    Marks a notification as read, then redirects to whatever it points to.
    get_object_or_404 with recipient=request.user prevents one user from
    marking/viewing another user's notification by guessing the pk.
    """
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    return redirect(notification.get_absolute_url())


@login_required
def feed_list_view(request):
    """Social-media style feed: browse all posts + comments, paginated."""
    query = request.GET.get("q", "").strip()

    feeds_qs = Feed.objects.select_related("author").prefetch_related("comments__author")

    if query:
        feeds_qs = feeds_qs.filter(
            models.Q(content__icontains=query)
            | models.Q(author__first_name__icontains=query)
            | models.Q(author__last_name__icontains=query)
        ).distinct()

    paginator = Paginator(feeds_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "feed_form": FeedForm(),
        "comment_form": FeedCommentForm(),
        "query": query,
    }
    return render(request, "feed/feed_list.html", context)


@login_required
@permission_required("feed.add_feed", raise_exception=True)
def feed_create_view(request):
    if request.method == "POST":
        form = FeedForm(request.POST)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.author = request.user
            feed.save()
        else:
            messages.error(request, "Could not post — please check your content.")

    return redirect("feed:list")


@login_required
@permission_required("feed.delete_feed", raise_exception=True)
def feed_delete_view(request, pk):
    feed = get_object_or_404(Feed, pk=pk)

    if feed.author_id != request.user.id:
        raise PermissionDenied("You can only delete your own posts.")

    if request.method == "POST":
        feed.delete()
        messages.info(request, "Post deleted.")

    return redirect("feed:list")


@login_required
@permission_required("feed.add_feedcomment", raise_exception=True)
def comment_create_view(request, pk):
    feed = get_object_or_404(Feed, pk=pk)

    if request.method == "POST":
        form = FeedCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.feed = feed
            comment.author = request.user
            comment.save()

            # Notify the post's author, unless they commented on their own post.
            if feed.author_id != request.user.id:
                Notification.objects.create(
                    recipient=feed.author,
                    type=NotificationType.FEED_COMMENT,
                    message=f"{request.user.get_full_name()} commented on your post: \"{comment.content[:50]}\"",
                )

    return redirect("feed:list")