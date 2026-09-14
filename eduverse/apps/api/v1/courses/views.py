from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.courses.models import Course, CourseStatus, Enrollment, EnrollmentStatus

from .serializers import CourseSerializer, EnrollmentSerializer

COURSE_TAGS = ["Courses"]
ENROLLMENT_TAGS = ["Enrollments"]


@extend_schema_view(
    list=extend_schema(
        summary="List courses",
        description="Teachers see their own courses (any status). Students see all published courses.",
        tags=COURSE_TAGS,
    ),
    retrieve=extend_schema(summary="Get a single course's details", tags=COURSE_TAGS),
    create=extend_schema(
        summary="Create a course",
        description="Teachers only. The authenticated teacher is automatically set as the course's owner.",
        tags=COURSE_TAGS,
    ),
    update=extend_schema(
        summary="Replace a course",
        description="Teachers may only edit their own courses.",
        tags=COURSE_TAGS,
    ),
    partial_update=extend_schema(
        summary="Partially update a course",
        description="Teachers may only edit their own courses.",
        tags=COURSE_TAGS,
    ),
    destroy=extend_schema(
        summary="Delete a course",
        description="Teachers may only delete their own courses.",
        tags=COURSE_TAGS,
    ),
)
class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return Course.objects.filter(teacher=user)
        return Course.objects.filter(status=CourseStatus.PUBLISHED)

    def perform_create(self, serializer):
        if not self.request.user.is_teacher:
            raise PermissionDenied("Only teachers can create courses.")
        serializer.save(teacher=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.teacher_id != self.request.user.id:
            raise PermissionDenied("You can only edit your own courses.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.teacher_id != self.request.user.id:
            raise PermissionDenied("You can only delete your own courses.")
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="List enrollments",
        description="Students see their own enrollments. Teachers see enrollments across their own courses.",
        tags=ENROLLMENT_TAGS,
    ),
    retrieve=extend_schema(summary="Get a single enrollment", tags=ENROLLMENT_TAGS),
    create=extend_schema(
        summary="Enrol in a course",
        description="Students only. Enrols the authenticated student with an active status.",
        tags=ENROLLMENT_TAGS,
    ),
)
class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return Enrollment.objects.filter(course__teacher=user)
        return Enrollment.objects.filter(student=user)

    def perform_create(self, serializer):
        if not self.request.user.is_student:
            raise PermissionDenied("Only students can enrol.")
        serializer.save(student=self.request.user, status=EnrollmentStatus.ACTIVE)