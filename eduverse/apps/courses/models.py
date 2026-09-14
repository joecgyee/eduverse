from django.conf import settings
from django.db import models


class CourseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class Course(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses_taught",
        limit_choices_to={"role": "teacher"},
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, null=True, blank=True)  # e.g. 'CS101'
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=CourseStatus.choices, default=CourseStatus.DRAFT
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    registration_open_date = models.DateField(null=True, blank=True)
    registration_close_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["teacher"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code + ' - ' if self.code else ''}{self.name}"


class CourseMaterial(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="materials"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="materials_uploaded",
        limit_choices_to={"role": "teacher"},
    )
    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_materials"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.course.name})"


class CourseMaterialAttachment(models.Model):
    """Allows multiple attachments per material post."""

    course_material = models.ForeignKey(
        CourseMaterial, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="course_materials/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_material_attachments"

    def __str__(self):
        return f"Attachment<{self.file.name}>"


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    BLOCKED = "blocked", "Blocked"


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "student"},
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    status = models.CharField(
        max_length=10, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "enrollments"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_student_course_enrollment"
            )
        ]
        indexes = [
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self):
        return f"{self.student.email} -> {self.course.name} ({self.status})"
    

class CourseFeedback(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="feedback"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_feedback_given",
        limit_choices_to={"role": "student"},
    )
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    comment = models.CharField(max_length=2000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_feedback"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "student"], name="unique_course_student_feedback"
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="feedback_rating_range",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback<{self.student.email} on {self.course.name}>"