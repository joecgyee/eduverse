from django.contrib import admin
from .models import *


class CourseMaterialAttachmentInline(admin.TabularInline):
    model = CourseMaterialAttachment
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "teacher", "status", "start_date", "end_date"]
    list_filter = ["status"]
    search_fields = ["name", "code", "teacher__email"]
    autocomplete_fields = ["teacher"]


@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "uploaded_by", "uploaded_at"]
    list_filter = ["course"]
    search_fields = ["title", "course__name"]
    autocomplete_fields = ["course", "uploaded_by"]
    inlines = [CourseMaterialAttachmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "status", "enrolled_at"]
    list_filter = ["course", "status"]
    search_fields = ["student__email", "course__name"]
    autocomplete_fields = ["student", "course"]
    actions = ["mark_blocked", "mark_active"]

    @admin.action(description="Block selected students from their course")
    def mark_blocked(self, request, queryset):
        queryset.update(status=EnrollmentStatus.BLOCKED)

    @admin.action(description="Reactivate selected enrollments")
    def mark_active(self, request, queryset):
        queryset.update(status=EnrollmentStatus.ACTIVE)


@admin.register(CourseFeedback)
class CourseFeedbackAdmin(admin.ModelAdmin):
    list_display = ["course", "student", "rating", "created_at"]
    list_filter = ["course", "rating"]
    search_fields = ["student__email", "course__name"]
    autocomplete_fields = ["course", "student"]