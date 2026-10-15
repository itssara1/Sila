from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Profile, User


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
        ]


class SkillChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.display_name


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

        fields = [
            "avatar",
            "bio",
            "wanted_skills",
            "resume",
            "portfolio_url",
        ]

        field_classes = {
            "wanted_skills": SkillChoiceField,
        }

        labels = {
            "avatar": _("Profile picture"),
            "bio": _("About you"),
            "wanted_skills": _("I want to learn"),
        }

        help_texts = {
            "avatar": _("JPG, PNG or WebP. Maximum size: 2 MB."),
        }

        widgets = {
            "avatar": forms.ClearableFileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
            "resume": forms.FileInput(attrs={"accept": "application/pdf"}),
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": _(
                        "Tell others about your skills "
                        "and what you would like to build."
                    ),
                }
            ),
            "wanted_skills": forms.CheckboxSelectMultiple(),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")

        # No new upload: keep the existing image or clear it.
        if not self.files.get("avatar"):
            return avatar

        if avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError(_("The image must be 2 MB or smaller."))

        image = getattr(avatar, "image", None)

        if image is None or image.format not in {
            "JPEG",
            "PNG",
            "WEBP",
        }:
            raise forms.ValidationError(_("Upload a JPG, PNG or WebP image."))

        if image.width > 4096 or image.height > 4096:
            raise forms.ValidationError(
                _("Image dimensions must not exceed 4096 × 4096 pixels.")
            )

        return avatar

    def clean_resume(self):
        upload = self.cleaned_data.get("resume")
        if not self.files.get("resume"):
            return upload
        if upload.size > 5 * 1024 * 1024:
            raise forms.ValidationError(_("The CV must be 5 MB or smaller."))
        if not upload.name.lower().endswith(".pdf") or upload.read(5) != b"%PDF-":
            raise forms.ValidationError(_("Upload a PDF file."))
        upload.seek(0)
        return upload
