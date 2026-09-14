from rest_framework import serializers

from apps.courses.models import Course, CourseFeedback, CourseMaterial, Enrollment


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id", "teacher", "teacher_name", "name", "code", "description",
            "status", "start_date", "end_date",
            "registration_open_date", "registration_close_date", "created_at",
        ]
        read_only_fields = ["id", "teacher", "created_at"]


class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        fields = ["id", "course", "title", "content", "uploaded_by", "uploaded_at"]
        read_only_fields = ["id", "uploaded_by", "uploaded_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_name", "course", "status", "enrolled_at"]
        read_only_fields = ["id", "student", "status", "enrolled_at"]


class CourseFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseFeedback
        fields = ["id", "course", "student", "rating", "comment", "created_at"]
        read_only_fields = ["id", "student", "created_at"]