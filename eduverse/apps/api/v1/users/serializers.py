from rest_framework import serializers

from apps.users.models import StudentProfile, TeacherProfile, User


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["date_of_birth", "bio"]


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ["department", "title"]


class UserSerializer(serializers.ModelSerializer):
    """Read-oriented representation, includes nested profile data."""

    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "photo", "date_joined", "student_profile", "teacher_profile",
        ]
        read_only_fields = ["id", "role", "date_joined"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Used for PATCH/PUT on one's own account — excludes role/email changes here for safety."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "photo"]