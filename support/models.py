from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Feedback(models.Model):
    class Category(models.TextChoices):
        TECHNICAL = "technical", _("Technical issue")
        SUGGESTION = "suggestion", _("Suggestion")
        GENERAL = "general", _("General feedback")

    class Status(models.TextChoices):
        NEW = "new", _("New")
        IN_PROGRESS = "in_progress", _("In progress")
        CLOSED = "closed", _("Closed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="feedback_messages",
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
        verbose_name=_("Message type"),
    )

    subject = models.CharField(
        max_length=150,
        verbose_name=_("Subject"),
    )

    message = models.TextField(
        max_length=3000,
        verbose_name=_("Message"),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name=_("Status"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedback messages")

    def __str__(self):
        return self.subject
