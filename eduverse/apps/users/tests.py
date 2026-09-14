from django.test import TestCase
from django.urls import reverse

from .models import StudentProfile, TeacherProfile, User, UserRole


class UserManagerTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass1234", first_name="A", last_name="B", role=UserRole.STUDENT)

    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            email="student@example.com", password="pass1234",
            first_name="Ann", last_name="Lee", role=UserRole.STUDENT,
        )
        self.assertNotEqual(user.password, "pass1234")
        self.assertTrue(user.check_password("pass1234"))
        self.assertFalse(user.is_staff)

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password="pass1234", first_name="Admin", last_name="User",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, UserRole.TEACHER)


class UserModelTests(TestCase):
    def test_is_student_and_is_teacher_properties(self):
        student = User.objects.create_user(
            email="s@example.com", password="pass1234", first_name="S", last_name="One", role=UserRole.STUDENT,
        )
        teacher = User.objects.create_user(
            email="t@example.com", password="pass1234", first_name="T", last_name="One", role=UserRole.TEACHER,
        )
        self.assertTrue(student.is_student)
        self.assertFalse(student.is_teacher)
        self.assertTrue(teacher.is_teacher)

    def test_get_full_name(self):
        user = User.objects.create_user(
            email="a@example.com", password="pass1234", first_name="Jane", last_name="Doe", role=UserRole.STUDENT,
        )
        self.assertEqual(user.get_full_name(), "Jane Doe")


class RoleGroupSignalTests(TestCase):
    """Confirms apps/users/signals.py assigns the correct auth Group on creation."""

    def test_student_added_to_student_group(self):
        student = User.objects.create_user(
            email="s2@example.com", password="pass1234", first_name="S", last_name="Two", role=UserRole.STUDENT,
        )
        self.assertTrue(student.groups.filter(name="Student").exists())
        self.assertFalse(student.groups.filter(name="Teacher").exists())

    def test_teacher_added_to_teacher_group(self):
        teacher = User.objects.create_user(
            email="t2@example.com", password="pass1234", first_name="T", last_name="Two", role=UserRole.TEACHER,
        )
        self.assertTrue(teacher.groups.filter(name="Teacher").exists())


class RegisterViewTests(TestCase):
    def test_get_register_page(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)

    def test_post_register_creates_student_and_profile(self):
        response = self.client.post(reverse("users:register"), {
            "email": "newstudent@example.com", "first_name": "New", "last_name": "Student",
            "role": UserRole.STUDENT, "date_of_birth": "2000-01-01",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("users:login"))
        user = User.objects.get(email="newstudent@example.com")
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())

    def test_post_register_creates_teacher_and_profile(self):
        response = self.client.post(reverse("users:register"), {
            "email": "newteacher@example.com", "first_name": "New", "last_name": "Teacher",
            "role": UserRole.TEACHER, "title": "Dr.", "department": "Computer Science",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("users:login"))
        user = User.objects.get(email="newteacher@example.com")
        self.assertTrue(TeacherProfile.objects.filter(user=user).exists())

    def test_password_mismatch_blocks_creation(self):
        self.client.post(reverse("users:register"), {
            "email": "mismatch@example.com", "first_name": "A", "last_name": "B",
            "role": UserRole.STUDENT, "date_of_birth": "2000-01-01",
            "password1": "StrongPass123!", "password2": "DifferentPass123!",
        })
        self.assertFalse(User.objects.filter(email="mismatch@example.com").exists())


class LoginLogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="login@example.com", password="pass1234", first_name="Log", last_name="In", role=UserRole.STUDENT,
        )
        StudentProfile.objects.create(user=self.user, date_of_birth="2000-01-01")

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(reverse("users:login"), {"username": "login@example.com", "password": "pass1234"})
        self.assertRedirects(response, reverse("users:dashboard"))

    def test_login_wrong_password_rejected(self):
        response = self.client.post(reverse("users:login"), {"username": "login@example.com", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_ends_session(self):
        self.client.login(email="login@example.com", password="pass1234")
        self.client.get(reverse("users:logout"))
        response = self.client.get(reverse("users:detail"))
        self.assertEqual(response.status_code, 302)


class UserDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="me@example.com", password="pass1234", first_name="Me", last_name="User", role=UserRole.STUDENT,
        )
        StudentProfile.objects.create(user=self.user, date_of_birth="2000-01-01")
        self.other = User.objects.create_user(
            email="other@example.com", password="pass1234", first_name="Other", last_name="User", role=UserRole.STUDENT,
        )
        StudentProfile.objects.create(user=self.other, date_of_birth="2000-01-01")

    def test_requires_login(self):
        self.assertEqual(self.client.get(reverse("users:detail")).status_code, 302)

    def test_own_profile_flags_is_own_profile_true(self):
        self.client.login(email="me@example.com", password="pass1234")
        response = self.client.get(reverse("users:detail"))
        self.assertTrue(response.context["is_own_profile"])

    def test_viewing_other_profile_flags_false(self):
        self.client.login(email="me@example.com", password="pass1234")
        response = self.client.get(reverse("users:detail_by_id", args=[self.other.pk]))
        self.assertFalse(response.context["is_own_profile"])