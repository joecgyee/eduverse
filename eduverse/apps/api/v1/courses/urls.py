from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register("", CourseViewSet, basename="course")

urlpatterns = router.urls