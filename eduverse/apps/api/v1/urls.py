from django.urls import include, path

urlpatterns = [
    path("users/", include("apps.api.v1.users.urls")),
    path("courses/", include("apps.api.v1.courses.urls")),
    path("feed/", include("apps.api.v1.feed.urls")),
    path("chat/", include("apps.api.v1.chat.urls")),
]