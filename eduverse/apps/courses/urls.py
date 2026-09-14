from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list_view, name="list"),
    path("create/", views.course_create_view, name="create"),
    path("<int:pk>/", views.course_detail_view, name="detail"),
    path("<int:pk>/edit/", views.course_update_view, name="update"),
    path("<int:pk>/students/", views.course_students_view, name="students"),
    path("<int:pk>/students/<int:enrollment_id>/block/", views.block_student_view, name="block_student"),
    path("<int:pk>/materials/add/", views.course_material_create_view, name="material_create"),
    path("<int:pk>/materials/<int:material_id>/edit/", views.course_material_update_view, name="material_update"),
    path("<int:pk>/materials/<int:material_id>/delete/", views.course_material_delete_view, name="material_delete"),
    path("<int:pk>/enrol/", views.enrol_view, name="enrol"),
    path("<int:pk>/classmates/", views.course_classmates_view, name="classmates"),
    path("<int:pk>/feedback/", views.course_feedback_create_view, name="feedback_create"),
]