from django.urls import path

from . import views

app_name = "feed"

urlpatterns = [
    path("", views.feed_list_view, name="list"),
    path("create/", views.feed_create_view, name="create"),
    path("<int:pk>/delete/", views.feed_delete_view, name="delete"),
    path("<int:pk>/comments/", views.comment_create_view, name="comment_create"),
    path("notifications/<int:pk>/", views.notification_redirect_view, name="notification_redirect"),
]