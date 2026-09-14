def notifications(request):
    """
    Injects the current user's 5 most recent notifications into every
    template's context (read or unread), so navbar.html can display them.
    The red dot only shows if at least one is still unread.
    """
    if not request.user.is_authenticated:
        return {"notifications": [], "has_unread_notifications": False}

    return {
        "notifications": request.user.notifications.order_by("-created_at")[:5],
        "has_unread_notifications": request.user.notifications.filter(is_read=False).exists(),
    }