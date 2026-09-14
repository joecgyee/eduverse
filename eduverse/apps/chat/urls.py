from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_rooms_list_view, name="list"),
    path("start/", views.chat_room_start_view, name="start"),
    path("course/<int:course_pk>/create/", views.chat_room_create_view, name="create"),
    path("<int:pk>/", views.chat_room_detail_view, name="room_detail"),
    path("ajax/course/<int:course_pk>/members/", views.course_members_ajax_view, name="course_members_ajax"),
    path("<int:pk>/upload/", views.chat_attachment_upload_view, name="upload_attachment"),
]