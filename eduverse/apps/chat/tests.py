from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.courses.models import Course, CourseStatus, Enrollment, EnrollmentStatus
from apps.users.models import StudentProfile, TeacherProfile, User, UserRole

from .forms import ChatRoomCreateForm
from .models import ChatRoom, ChatRoomMember


def create_teacher(email="teacher@example.com"):
    user = User.objects.create_user(email=email, password="pass1234", first_name="T", last_name="One", role=UserRole.TEACHER)
    TeacherProfile.objects.create(user=user, department="CS", title="Dr.")
    return user


def create_student(email="student@example.com"):
    user = User.objects.create_user(email=email, password="pass1234", first_name="S", last_name="One", role=UserRole.STUDENT)
    StudentProfile.objects.create(user=user, date_of_birth="2000-01-01")
    return user


class ChatRoomAutoCreationSignalTests(TestCase):
    """Creating a Course should auto-create its ChatRoom with the teacher as a member."""

    def test_room_created_with_correct_name(self):
        teacher = create_teacher()
        course = Course.objects.create(teacher=teacher, name="Algorithms", code="CS201")
        room = ChatRoom.objects.get(course=course)
        self.assertEqual(room.name, "CS201 - Algorithms")
        self.assertEqual(room.created_by, teacher)

    def test_teacher_is_added_as_member(self):
        teacher = create_teacher()
        course = Course.objects.create(teacher=teacher, name="Databases", code="CS202")
        room = ChatRoom.objects.get(course=course)
        self.assertTrue(ChatRoomMember.objects.filter(room=room, user=teacher).exists())


class EnrollmentAddsMemberSignalTests(TestCase):
    def test_active_enrollment_adds_student_to_room(self):
        student = create_student()
        course = Course.objects.create(teacher=create_teacher(), name="Networks", code="CS203", status=CourseStatus.PUBLISHED)
        room = ChatRoom.objects.get(course=course)
        Enrollment.objects.create(student=student, course=course, status=EnrollmentStatus.ACTIVE)
        self.assertTrue(ChatRoomMember.objects.filter(room=room, user=student).exists())

    def test_blocked_enrollment_does_not_add_member(self):
        student = create_student()
        course = Course.objects.create(teacher=create_teacher(), name="Security", code="CS204", status=CourseStatus.PUBLISHED)
        room = ChatRoom.objects.get(course=course)
        Enrollment.objects.create(student=student, course=course, status=EnrollmentStatus.BLOCKED)
        self.assertFalse(ChatRoomMember.objects.filter(room=room, user=student).exists())


class ChatRoomMemberModelTests(TestCase):
    def test_unique_room_member_constraint(self):
        teacher = create_teacher()
        course = Course.objects.create(teacher=teacher, name="Course X")
        room = ChatRoom.objects.get(course=course)  # teacher already added by signal
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ChatRoomMember.objects.create(room=room, user=teacher)


class ChatRoomsListViewTests(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()
        self.course = Course.objects.create(teacher=self.teacher, name="Course Y", status=CourseStatus.PUBLISHED)
        self.room = ChatRoom.objects.get(course=self.course)

    def test_requires_login(self):
        self.assertEqual(self.client.get(reverse("chat:list")).status_code, 302)

    def test_teacher_sees_own_course_room(self):
        self.client.login(email="teacher@example.com", password="pass1234")
        response = self.client.get(reverse("chat:list"))
        self.assertIn(self.room, response.context["rooms"])

    def test_non_enrolled_student_does_not_see_room(self):
        self.client.login(email="student@example.com", password="pass1234")
        response = self.client.get(reverse("chat:list"))
        self.assertNotIn(self.room, response.context["rooms"])

    def test_enrolled_student_sees_room(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(email="student@example.com", password="pass1234")
        response = self.client.get(reverse("chat:list"))
        self.assertIn(self.room, response.context["rooms"])


class ChatRoomDetailViewTests(TestCase):
    def setUp(self):
        self.teacher = create_teacher()
        self.student = create_student()
        self.outsider = create_student(email="outsider@example.com")
        self.course = Course.objects.create(teacher=self.teacher, name="Course Z", status=CourseStatus.PUBLISHED)
        self.room = ChatRoom.objects.get(course=self.course)
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_member_can_view_room(self):
        self.client.login(email="student@example.com", password="pass1234")
        self.assertEqual(self.client.get(reverse("chat:room_detail", args=[self.room.pk])).status_code, 200)

    def test_non_member_forbidden(self):
        self.client.login(email="outsider@example.com", password="pass1234")
        self.assertEqual(self.client.get(reverse("chat:room_detail", args=[self.room.pk])).status_code, 403)


class ChatRoomCreateFormTests(TestCase):
    def setUp(self):
        self.student = create_student()
        self.classmate = create_student(email="classmate@example.com")
        self.course = Course.objects.create(teacher=create_teacher(), name="Form Course", status=CourseStatus.PUBLISHED)
        Enrollment.objects.create(student=self.student, course=self.course)
        Enrollment.objects.create(student=self.classmate, course=self.course)

    def test_valid_members_pass_validation(self):
        form = ChatRoomCreateForm(
            data={"name": "Study group", "course": self.course.pk, "members": [self.classmate.pk]}, user=self.student,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_member_outside_course_fails_validation(self):
        stranger = create_student(email="stranger@example.com")
        form = ChatRoomCreateForm(
            data={"name": "Study group", "course": self.course.pk, "members": [stranger.pk]}, user=self.student,
        )
        self.assertFalse(form.is_valid())