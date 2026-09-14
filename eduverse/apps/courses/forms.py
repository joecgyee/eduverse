from django import forms
from django.forms import inlineformset_factory

from .models import Course, CourseFeedback, CourseMaterial, CourseMaterialAttachment


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "name", "code", "description", "status",
            "start_date", "end_date",
            "registration_open_date", "registration_close_date",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "registration_open_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "registration_close_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date cannot be before start date.")

        reg_open = cleaned_data.get("registration_open_date")
        reg_close = cleaned_data.get("registration_close_date")
        if reg_open and reg_close and reg_close < reg_open:
            self.add_error("registration_close_date", "Registration close date cannot be before open date.")

        return cleaned_data


class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


# Allows uploading several files at once alongside one CourseMaterial post.
CourseMaterialAttachmentFormSet = inlineformset_factory(
    CourseMaterial,
    CourseMaterialAttachment,
    fields=["file"],
    extra=3,
    can_delete=True,
    widgets={"file": forms.ClearableFileInput(attrs={"class": "form-control"})},
)


class CourseFeedbackForm(forms.ModelForm):
    class Meta:
        model = CourseFeedback
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(
                choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)],
                attrs={"class": "form-select"},
            ),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }