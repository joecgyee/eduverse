from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.feed.models import Notification, NotificationType
from apps.users.models import StudentProfile, TeacherProfile, User, UserRole

from .models import Course, CourseFeedback, CourseStatus, Enrollment, EnrollmentStatus


def create_teacher(email="teacher@example.com"):
    user = User.objects.create_user(email=email, password="pass1234", first_name="T", last_name="One", role=UserRole.TEACHER)
    TeacherProfile.objects.create(user=user, department="CS", title="Dr.")
    return user


def create_student(email="student@example.com"):
    user = User.objects.create_user(email=email, password="pass1234", first_name="S", last_name="One", role=UserRole.STUDENT)
    StudentProfile.objects.create(user=user, date_of_birth="2000-01-01")
    return user


class CourseModelTests(TestCase):
    def test_str_includes_code_and_name(self):
        course = Course.objects.create(teacher=create_teacher(), name="Intro to CS", code="CS101")
        self.assertEqual(str(course), "CS101 - Intro to CS")

    def test_default_status_is_draft(self):
        course = Course.objects.create(teacher=create_teacher(), name="No Status Set")
        self.assertEqual(course.status, CourseStatus.DRAFT)


class EnrollmentModelTests(TestCase):
    def test_unique_student_course_constraint(self):
        student = create_student()
        course = Course.objects.create(teacher=create_teacher(), name="Course A", status=CourseStatus.PUBLISHED)
        Enrollment.objects.create(student=student, course=course)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Enrollment.objects.create(student=student, course=course)

    def test_default_status_active(self):
        student = create_student()
        course = Course.objects.create(teacher=create_teacher(), name="Course B", status=CourseStatus.PUBLISHED)
        enrollment = Enrollment.objects.create(student=student, course=course)
        self.assertEqual(enrollment.status, EnrollmentStatus.ACTIVE)


class CourseFeedbackModelTests(TestCase):
    def test_rating_out_of_range_violates_check_constraint(self):
        student, course = create_student(), Course.objects.create(teacher=create_teacher(), name="Course C")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CourseFeedback.objects.create(course=course, student=student, rating=6)

    def test_unique_course_student_feedback(self):
        student, course = create_student(), Course.objects.create(teacher=create_teacher(), name="Course D")
        CourseFeedback.objects.create(course=course, student=student, rating=5)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CourseFeedback.objects.create(course=course, student=student, rating=4)


class CourseListViewTests(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()
        self.my_draft = Course.objects.create(teacher=self.teacher, name="Draft Course", status=CourseStatus.DRAFT)
        self.published = Course.objects.create(
            teacher=create_teacher(email="teacher2@example.com"), name="Published Course", status=CourseStatus.PUBLISHED
        )

    def test_teacher_sees_own_courses_any_status(self):
        self.client.login(email="teacher@example.com", password="pass1234")
        response = self.client.get(reverse("courses:list"))
        self.assertIn(self.my_draft, response.context["my_courses_page"].object_list)

    def test_student_sees_published_not_draft(self):
        self.client.login(email="student@example.com", password="pass1234")
        response = self.client.get(reverse("courses:list"))
        ids = [c.id for c in response.context["published_page"].object_list]
        self.assertIn(self.published.id, ids)
        self.assertNotIn(self.my_draft.id, ids)


class EnrolViewTests(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()
        self.course = Course.objects.create(teacher=self.teacher, name="Course E", status=CourseStatus.PUBLISHED)

    def test_student_can_enrol_and_teacher_is_notified(self):
        self.client.login(email="student@example.com", password="pass1234")
        self.client.post(reverse("courses:enrol", args=[self.course.pk]))
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course, status=EnrollmentStatus.ACTIVE).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.teacher, type=NotificationType.ENROLLMENT).exists())

    def test_blocked_student_cannot_reenrol(self):
        Enrollment.objects.create(student=self.student, course=self.course, status=EnrollmentStatus.BLOCKED)
        self.client.login(email="student@example.com", password="pass1234")
        self.client.post(reverse("courses:enrol", args=[self.course.pk]))
        self.assertEqual(Enrollment.objects.get(student=self.student, course=self.course).status, EnrollmentStatus.BLOCKED)


class BlockStudentViewTests(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.other_teacher = create_teacher(email="teacher3@example.com")
        self.student = create_student()
        self.course = Course.objects.create(teacher=self.teacher, name="Course F", status=CourseStatus.PUBLISHED)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)

    def test_owner_teacher_can_block_student(self):
        self.client.login(email="teacher@example.com", password="pass1234")
        self.client.post(reverse("courses:block_student", args=[self.course.pk, self.enrollment.pk]))
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, EnrollmentStatus.BLOCKED)

    def test_non_owner_teacher_forbidden(self):
        self.client.login(email="teacher3@example.com", password="pass1234")
        response = self.client.post(reverse("courses:block_student", args=[self.course.pk, self.enrollment.pk]))
        self.assertEqual(response.status_code, 403)


class CourseFeedbackViewTests(TestCase):
    def setUp(self):
        self.student = create_student()
        self.course = Course.objects.create(teacher=create_teacher(), name="Course G", status=CourseStatus.PUBLISHED)

    def test_non_enrolled_student_forbidden(self):
        self.client.login(email="student@example.com", password="pass1234")
        response = self.client.get(reverse("courses:feedback_create", args=[self.course.pk]))
        self.assertEqual(response.status_code, 403)

    def test_enrolled_student_can_submit_feedback(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(email="student@example.com", password="pass1234")
        self.client.post(reverse("courses:feedback_create", args=[self.course.pk]), {"rating": 5, "comment": "Great!"})
        self.assertTrue(CourseFeedback.objects.filter(course=self.course, student=self.student).exists())