from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

U = settings.AUTH_USER_MODEL


class Team(models.Model):
    class Category(models.TextChoices):
        HACKATHON = "hackathon", _("Hackathon")
        CHALLENGE = "challenge", _("Challenge")
        FREELANCE = "freelance", _("Freelance collaboration")

    owner = models.ForeignKey(U, on_delete=models.PROTECT, related_name="teams_led")
    title = models.CharField(max_length=150, verbose_name=_("Project title"))
    category = models.CharField(
        max_length=20, choices=Category.choices, verbose_name=_("Category")
    )
    description = models.TextField(
        max_length=3000, verbose_name=_("Project description")
    )
    contribution = models.TextField(
        max_length=1000, verbose_name=_("Your contribution as leader")
    )
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title


class Role(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="roles")
    title = models.CharField(max_length=100, verbose_name=_("Role title"))
    description = models.TextField(max_length=1000, verbose_name=_("Role description"))
    seats = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name=_("Number of seats"),
    )
    skills = models.ManyToManyField(
        "skills.Skill",
        blank=True,
        related_name="team_roles",
        verbose_name=_("Required skills"),
    )

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(seats__gte=1, seats__lte=20), name="role_seats_1_20"
            )
        ]

    @property
    def available(self):
        return max(0, self.seats - self.memberships.count())

    def __str__(self):
        return self.title


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Under review")
        ACCEPTED = "accepted", _("Accepted")
        REJECTED = "rejected", _("Rejected")
        WITHDRAWN = "withdrawn", _("Withdrawn")

    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="applications"
    )
    applicant = models.ForeignKey(
        U, on_delete=models.PROTECT, related_name="team_applications"
    )
    message = models.TextField(
        max_length=1500, verbose_name=_("Why would you like to join?")
    )
    share_resume = models.BooleanField(
        default=False, verbose_name=_("Share my CV with this team leader")
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    leader_note = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["role", "applicant"], name="one_application_per_role"
            )
        ]


class Membership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="memberships")
    user = models.ForeignKey(
        U, on_delete=models.PROTECT, related_name="team_memberships"
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"], name="one_membership_per_team"
            )
        ]


class TeachingSkill(models.Model):
    class Level(models.TextChoices):
        INTERMEDIATE = "intermediate", _("Intermediate")
        ADVANCED = "advanced", _("Advanced")

    user = models.ForeignKey(
        U, on_delete=models.CASCADE, related_name="teaching_skills"
    )
    skill = models.ForeignKey(
        "skills.Skill", on_delete=models.PROTECT, related_name="teachers"
    )
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.INTERMEDIATE,
        verbose_name=_("Your level"),
    )
    description = models.TextField(
        max_length=500, blank=True, verbose_name=_("What can you help with?")
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "skill"], name="unique_teaching_skill"
            )
        ]


class LearningRequest(models.Model):
    class Kind(models.TextChoices):
        LEARN = "learn", _("Learning request")
        EXCHANGE = "exchange", _("Skill exchange")

    class Status(models.TextChoices):
        PENDING = "pending", _("Under review")
        ACCEPTED = "accepted", _("Accepted")
        REJECTED = "rejected", _("Rejected")
        CANCELLED = "cancelled", _("Cancelled")

    sender = models.ForeignKey(
        U, on_delete=models.PROTECT, related_name="learning_sent"
    )
    recipient = models.ForeignKey(
        U, on_delete=models.PROTECT, related_name="learning_received"
    )
    teaching = models.ForeignKey(
        TeachingSkill, on_delete=models.PROTECT, related_name="requests"
    )
    offered_skill = models.ForeignKey(
        TeachingSkill,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="exchange_requests",
        verbose_name=_("Skill I offer in return"),
    )
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.LEARN,
        verbose_name=_("Request type"),
    )
    message = models.TextField(
        max_length=1500, verbose_name=_("Introduce yourself and your learning goal")
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(sender=F("recipient")), name="no_self_learning"
            ),
            models.UniqueConstraint(
                fields=["sender", "teaching"],
                condition=Q(status__in=["pending", "accepted"]),
                name="one_active_learning_request",
            ),
        ]


class Conversation(models.Model):
    team = models.OneToOneField(
        Team,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="conversation",
    )
    learning = models.OneToOneField(
        LearningRequest,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="conversation",
    )
    participants = models.ManyToManyField(U, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(team__isnull=False, learning__isnull=True)
                    | Q(team__isnull=True, learning__isnull=False)
                ),
                name="conversation_has_one_context",
            )
        ]

    @property
    def title(self):
        return (
            self.team.title
            if self.team_id
            else self.learning.teaching.skill.display_name
        )


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(U, on_delete=models.PROTECT)
    body = models.TextField(max_length=2000, verbose_name=_("Message"))
    client_id = models.UUIDField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["pk"]
