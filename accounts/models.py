from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    pass


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, max_length=255)
    bio = models.TextField(max_length=500, blank=True, verbose_name=_("About you"))
    resume = models.FileField(
        upload_to="private/resumes/%Y/%m/", blank=True, verbose_name=_("CV (PDF)")
    )
    portfolio_url = models.URLField(blank=True, verbose_name=_("Portfolio link"))
    wanted_skills = models.ManyToManyField(
        "skills.Skill",
        blank=True,
        related_name="interested_profiles",
        verbose_name=_("I want to learn"),
    )

    def __str__(self):
        return self.user.username
