from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import Team, Role, Application, TeachingSkill, LearningRequest, Message


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["title", "category", "description", "contribution"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "contribution": forms.Textarea(attrs={"rows": 3}),
        }


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["title", "description", "seats", "skills"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "skills": forms.CheckboxSelectMultiple(),
        }


RoleFormSet = inlineformset_factory(
    Team,
    Role,
    form=RoleForm,
    extra=0,
    min_num=1,
    validate_min=True,
    max_num=12,
    validate_max=True,
    can_delete=True,
)


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["message", "share_resume"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}


class TeachingForm(forms.ModelForm):
    class Meta:
        model = TeachingSkill
        fields = ["skill", "level", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class LearningForm(forms.ModelForm):
    class Meta:
        model = LearningRequest
        fields = ["kind", "offered_skill", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["offered_skill"].queryset = TeachingSkill.objects.filter(
            user=user
        ).select_related("skill")
        self.fields["offered_skill"].label_from_instance = (
            lambda obj: obj.skill.display_name
        )

    def clean(self):
        d = super().clean()
        if d.get("kind") == "exchange" and not d.get("offered_skill"):
            self.add_error("offered_skill", _("Choose a skill to offer in exchange."))
        if d.get("kind") == "learn":
            d["offered_skill"] = None
        return d
