from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import StudentProfile, TeacherProfile, TeacherTitle, User, UserRole


class RegisterForm(forms.ModelForm):
    """
    Handles account creation for both roles. Role-specific fields
    (date_of_birth / department / title) are optional at the form level
    and validated conditionally based on the chosen role.
    """

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    # Student-only
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    # Teacher-only
    department = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    title = forms.ChoiceField(
        choices=TeacherTitle.choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role", "photo"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")

        if role == UserRole.STUDENT and not cleaned_data.get("date_of_birth"):
            self.add_error("date_of_birth", "Date of birth is required for students.")

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        if password1:
            try:
                validate_password(password1)
            except ValidationError as e:
                self.add_error("password1", e)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            if user.role == UserRole.STUDENT:
                StudentProfile.objects.create(
                    user=user,
                    date_of_birth=self.cleaned_data["date_of_birth"],
                    bio="",
                )
            else:
                TeacherProfile.objects.create(
                    user=user,
                    department=self.cleaned_data.get("department"),
                    title=self.cleaned_data.get("title"),
                )
        return user


class LoginForm(AuthenticationForm):
    """
    AuthenticationForm's first field is auto-named 'username' regardless
    of USERNAME_FIELD, so relabel it to avoid confusing the template/user.
    """

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "photo"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["date_of_birth", "bio"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class TeacherProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ["department", "title"]
        widgets = {
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.Select(attrs={"class": "form-select"}),
        }