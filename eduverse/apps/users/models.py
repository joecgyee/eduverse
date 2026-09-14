from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"


class UserManager(BaseUserManager):
    """
    Custom manager for the email-based User model.
    Required because AbstractBaseUser ships with no manager at all.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.TEACHER)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model, authenticated by email instead of username.
    role determines whether a StudentProfile or TeacherProfile applies.
    """

    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
    )
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    photo = models.ImageField(upload_to="user_photos/%Y/%m/", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT

    @property
    def is_teacher(self):
        return self.role == UserRole.TEACHER


class StudentProfile(models.Model):
    """
    Student-only fields, 1:1 with User where role == student.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="student_profile",
        limit_choices_to={"role": UserRole.STUDENT},
    )
    date_of_birth = models.DateField()
    bio = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "student_profiles"

    def __str__(self):
        return f"{self.user.get_full_name}'s Profile <{self.user.email}>"

class TeacherTitle(models.TextChoices):
    DR = "Dr.", "Dr."
    PROF = "Prof.", "Prof."
    MR = "Mr.", "Mr."
    MS = "Ms.", "Ms."
    MRS = "Mrs.", "Mrs."

class TeacherProfile(models.Model):
    """
    Teacher-only fields, 1:1 with User where role == teacher.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="teacher_profile",
        limit_choices_to={"role": UserRole.TEACHER},
    )
    department = models.CharField(max_length=150, null=True, blank=True)
    title = models.CharField(
            max_length=10,
            choices=TeacherTitle.choices,
            null=True,
            blank=True,
        )
    
    class Meta:
        db_table = "teacher_profiles"

    def __str__(self):
        return f"{self.user.get_full_name}'s Profile <{self.user.email}>"