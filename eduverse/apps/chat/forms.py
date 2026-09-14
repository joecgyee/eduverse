from django import forms

from apps.courses.models import Course, Enrollment, EnrollmentStatus
from apps.users.models import User

from django.db.models import Q

from .models import ChatMessage



class ChatRoomCreateForm(forms.Form):
    name = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional room name"}),
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_course"}),
    )
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6, "id": "id_members"}),
        required=False,
        help_text="Hold Ctrl/Cmd to select multiple classmates or your teacher.",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        enrolled_course_ids = Enrollment.objects.filter(
            student=user, status=EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)
        self.fields["course"].queryset = Course.objects.filter(id__in=enrolled_course_ids)

        # Populate 'members' queryset broadly (needed so ModelMultipleChoiceField
        # can validate submitted IDs); clean() below still enforces the real
        # course-specific restriction as the source of truth.
        self.fields["members"].queryset = User.objects.filter(
            Q(courses_taught__id__in=enrolled_course_ids)
            | Q(enrollments__course_id__in=enrolled_course_ids, enrollments__status=EnrollmentStatus.ACTIVE)
        ).exclude(id=user.id).distinct()

        # If a course was already submitted (e.g. form re-render after a
        # validation error), keep the dropdown populated so selections aren't lost.
        if "course" in self.data:
            try:
                course_id = int(self.data.get("course"))
                self._populate_members_for_course(course_id)
            except (TypeError, ValueError):
                pass

    def _populate_members_for_course(self, course_id):
        student_ids = Enrollment.objects.filter(
            course_id=course_id, status=EnrollmentStatus.ACTIVE
        ).exclude(student=self.user).values_list("student_id", flat=True)
        course = Course.objects.filter(id=course_id).first()
        ids = list(student_ids)
        if course:
            ids.append(course.teacher_id)
        self.fields["members"].queryset = User.objects.filter(id__in=ids)

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        members = cleaned_data.get("members")

        if course and members:
            valid_ids = set(
                Enrollment.objects.filter(course=course, status=EnrollmentStatus.ACTIVE)
                .values_list("student_id", flat=True)
            )
            valid_ids.add(course.teacher_id)
            invalid = [m for m in members if m.id not in valid_ids]
            if invalid:
                self.add_error("members", "Selected members must share the chosen course with you.")

        return cleaned_data


class ChatAttachmentForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ["attachment"]
        widgets = {
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control", "id": "id_attachment"}),
        }

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")
        if attachment and attachment.size > 10 * 1024 * 1024:  # 10 MB cap
            raise forms.ValidationError("File too large. Maximum size is 10MB.")
        return attachment