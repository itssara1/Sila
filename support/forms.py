from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback

        fields = [
            "category",
            "subject",
            "message",
        ]

        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "placeholder": _("A short title for your message"),
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 7,
                    "placeholder": _("Tell us what happened or share your suggestion."),
                }
            ),
        }

        help_texts = {
            "message": _(
                "For technical issues, mention the page and what you "
                "were trying to do. Do not include passwords."
            ),
        }

    def clean_subject(self):
        subject = self.cleaned_data["subject"].strip()

        if len(subject) < 5:
            raise forms.ValidationError(_("Write a subject of at least 5 characters."))

        return subject

    def clean_message(self):
        message = self.cleaned_data["message"].strip()

        if len(message) < 20:
            raise forms.ValidationError(_("Write a message of at least 20 characters."))

        return message
