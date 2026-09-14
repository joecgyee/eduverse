from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course, CourseStatus, Enrollment
from apps.feed.models import Feed
from apps.users.models import StudentProfile, TeacherProfile, User, UserRole


def create_teacher(email="teacher@example.com"):
    user = User.objects.create_user(email=email, password="pass1234", first_name="T", last_name="One", role=UserRole.TEACHER)
    TeacherProfile.objects.create(user=user, department="CS", title="Dr.")
    return user


def create_student(email="student@example.com"):
    user = User.objects.create_user(email=email, password="pass1234", first_name="S", last_name="One", role=UserRole.STUDENT)
    StudentProfile.objects.create(user=user, date_of_birth="2000-01-01")
    return user


def results(response):
    """Handles both paginated ({"results": [...]}) and plain list responses."""
    return response.data.get("results", response.data) if isinstance(response.data, dict) else response.data


class UserApiTests(APITestCase):
    def setUp(self):
        self.user = create_student()

    def test_list_requires_authentication(self):
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_endpoint_returns_own_data(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_search_filters_results(self):
        create_student(email="findme@example.com")
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/v1/users/", {"search": "findme"})
        self.assertIn("findme@example.com", [u["email"] for u in results(response)])

    def test_cannot_edit_other_users_profile(self):
        other = create_student(email="other@example.com")
        self.client.force_authenticate(self.user)
        response = self.client.patch(f"/api/v1/users/{other.pk}/", {"first_name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CourseApiTests(APITestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()

    def test_teacher_can_create_course(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post("/api/v1/courses/", {"name": "New Course", "code": "NC101"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(name="New Course", teacher=self.teacher).exists())

    def test_student_cannot_create_course(self):
        self.client.force_authenticate(self.student)
        response = self.client.post("/api/v1/courses/", {"name": "Should Fail"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_sees_only_published_courses(self):
        Course.objects.create(teacher=self.teacher, name="Draft", status=CourseStatus.DRAFT)
        Course.objects.create(teacher=self.teacher, name="Published", status=CourseStatus.PUBLISHED)
        self.client.force_authenticate(self.student)
        names = [c["name"] for c in results(self.client.get("/api/v1/courses/"))]
        self.assertIn("Published", names)
        self.assertNotIn("Draft", names)

    def test_teacher_cannot_edit_others_course(self):
        course = Course.objects.create(teacher=create_teacher(email="other_teacher@example.com"), name="Not Yours")
        self.client.force_authenticate(self.teacher)
        response = self.client.patch(f"/api/v1/courses/{course.pk}/", {"name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        course.refresh_from_db()
        self.assertEqual(course.name, "Not Yours")


class EnrollmentApiTests(APITestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()
        self.course = Course.objects.create(teacher=self.teacher, name="Course A", status=CourseStatus.PUBLISHED)

    def test_student_can_enrol_via_api(self):
        self.client.force_authenticate(self.student)
        response = self.client.post("/api/v1/courses/enrollments/", {"course": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_teacher_cannot_enrol_via_api(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post("/api/v1/courses/enrollments/", {"course": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FeedApiTests(APITestCase):
    def setUp(self):
        self.user = create_student()
        self.other = create_student(email="other2@example.com")

    def test_create_post(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/feed/", {"content": "Hello API"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_delete_others_post(self):
        feed = Feed.objects.create(author=self.other, content="Not yours")
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/v1/feed/{feed.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Feed.objects.filter(pk=feed.pk).exists())


class ChatRoomApiTests(APITestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()
        self.outsider = create_student(email="outsider2@example.com")
        self.course = Course.objects.create(teacher=self.teacher, name="Chat Course", status=CourseStatus.PUBLISHED)
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_member_sees_room_in_list(self):
        self.client.force_authenticate(self.student)
        names = [r["course_name"] for r in results(self.client.get("/api/v1/chat/"))]
        self.assertIn("Chat Course", names)

    def test_non_member_does_not_see_room(self):
        self.client.force_authenticate(self.outsider)
        names = [r["course_name"] for r in results(self.client.get("/api/v1/chat/"))]
        self.assertNotIn("Chat Course", names)