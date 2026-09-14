from django import forms

from .models import Feed, FeedComment


class FeedForm(forms.ModelForm):
    class Meta:
        model = Feed
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "What's on your mind?",
            }),
        }


class FeedCommentForm(forms.ModelForm):
    class Meta:
        model = FeedComment
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Write a comment...",
            }),
        }