from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("search/", views.user_search_view, name="search"),
    path("me/", views.user_detail_view, name="detail"),
    path("<int:pk>/", views.user_detail_view, name="detail_by_id"),
    path("me/edit/", views.user_update_view, name="update"),
]
 