import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import Q, Count, Max, F
from django.http import JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_GET
from accounts.models import Profile
from skills.models import Skill
from .models import (
    Team,
    Role,
    Application,
    Membership,
    TeachingSkill,
    LearningRequest,
    Conversation,
    Message,
)
from .forms import TeamForm, RoleFormSet, ApplicationForm, TeachingForm, LearningForm


def home(request):
    teams = (
        Team.objects.filter(is_open=True)
        .select_related("owner")
        .prefetch_related("roles__memberships")[:3]
    )
    return render(request, "community/home.html", {"teams": teams})


def explore(request):
    teams = Team.objects.select_related("owner").prefetch_related(
        "roles__memberships", "roles__skills"
    )
    q = request.GET.get("q", "").strip()[:150]
    category = request.GET.get("category", "")
    skill = request.GET.get("skill", "")
    status = request.GET.get("status", "open")
    if q:
        teams = teams.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(roles__title__icontains=q)
        )
    if category in Team.Category.values:
        teams = teams.filter(category=category)
    if skill.isdigit():
        teams = teams.filter(roles__skills__pk=skill)
    if status == "open":
        teams = teams.filter(is_open=True)
    elif status == "closed":
        teams = teams.filter(is_open=False)
    page = Paginator(teams.distinct(), 9).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "community/explore.html",
        {
            "page_obj": page,
            "q": q,
            "category": category,
            "selected_skill": skill,
            "status": status,
            "categories": Team.Category.choices,
            "skills": Skill.objects.all(),
            "filters": params.urlencode(),
        },
    )


@login_required
def team_create(request):
    team = Team(owner=request.user)
    form = TeamForm(request.POST or None, instance=team)
    roles = RoleFormSet(request.POST or None, instance=team, prefix="roles")
    if request.method == "POST" and form.is_valid() and roles.is_valid():
        with transaction.atomic():
            form.save()
            roles.save()
            chat = Conversation.objects.create(team=team)
            chat.participants.add(request.user)
        messages.success(request, _("Your team is now published."))
        return redirect("team_detail", pk=team.pk)
    return render(request, "community/team_form.html", {"form": form, "roles": roles})


def team_detail(request, pk):
    team = get_object_or_404(
        Team.objects.select_related("owner").prefetch_related(
            "roles__skills",
            "roles__memberships",
            "memberships__user",
            "memberships__role",
        ),
        pk=pk,
    )
    member = request.user.is_authenticated and (
        team.owner_id == request.user.pk
        or team.memberships.filter(user=request.user).exists()
    )
    applications = (
        Application.objects.filter(applicant=request.user, role__team=team)
        if request.user.is_authenticated
        else []
    )
    byrole = {a.role_id: a for a in applications}
    cards = [
        {"role": role, "application": byrole.get(role.pk)} for role in team.roles.all()
    ]
    return render(
        request,
        "community/team_detail.html",
        {"team": team, "role_cards": cards, "is_member": member},
    )


@login_required
def apply(request, pk):
    role = get_object_or_404(Role.objects.select_related("team"), pk=pk)
    team = role.team
    if team.owner_id == request.user.pk:
        raise PermissionDenied
    if (
        team.memberships.filter(user=request.user).exists()
        or role.applications.filter(applicant=request.user).exists()
    ):
        messages.info(request, _("You already applied or joined this team."))
        return redirect("team_detail", pk=team.pk)
    if not team.is_open or not role.available:
        messages.error(request, _("This role is no longer available."))
        return redirect("team_detail", pk=team.pk)
    form = ApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                # A write on the parent serializes both SQLite and row-locking database workflows.
                if not Team.objects.filter(pk=team.pk, is_open=True).update(
                    is_open=True
                ):
                    raise ValidationError(_("Recruitment has closed."))
                role.refresh_from_db()
                if (
                    not role.available
                    or team.memberships.filter(user=request.user).exists()
                ):
                    raise ValidationError(_("This role is no longer available."))
                application = form.save(commit=False)
                application.role = role
                application.applicant = request.user
                if (
                    application.share_resume
                    and not Profile.objects.filter(user=request.user)
                    .exclude(resume="")
                    .exists()
                ):
                    raise ValidationError(
                        _("Upload a CV in your profile before sharing it.")
                    )
                application.save()
        except (ValidationError, IntegrityError) as e:
            form.add_error(
                None,
                (
                    e.messages[0]
                    if isinstance(e, ValidationError)
                    else _("You already applied to this role.")
                ),
            )
        else:
            messages.success(
                request, _("Application sent. Track it in My applications.")
            )
            return redirect("applications")
    return render(
        request,
        "community/form.html",
        {
            "form": form,
            "heading": _("Apply to join"),
            "intro": role.title,
            "back": (
                team.get_absolute_url()
                if hasattr(team, "get_absolute_url")
                else "/teams/" + str(team.pk) + "/"
            ),
            "button": _("Send application"),
        },
    )


@login_required
def applicants(request, pk):
    team = get_object_or_404(Team, pk=pk, owner=request.user)
    applications = (
        Application.objects.filter(role__team=team)
        .select_related("role", "applicant__profile")
        .prefetch_related("applicant__teaching_skills__skill")
    )
    return render(
        request,
        "community/applicants.html",
        {"team": team, "applications": applications},
    )


@login_required
@require_POST
def application_decide(request, pk, decision):
    application = get_object_or_404(
        Application.objects.select_related("role__team"),
        pk=pk,
        role__team__owner=request.user,
    )
    team = application.role.team
    if decision not in ["accept", "reject", "note"]:
        raise PermissionDenied
    try:
        with transaction.atomic():
            Team.objects.filter(pk=team.pk).update(is_open=F("is_open"))
            team.refresh_from_db()
            application.refresh_from_db()
            if decision == "note":
                application.leader_note = request.POST.get("note", "").strip()[:1000]
                application.save(update_fields=["leader_note"])
            else:
                if application.status != "pending":
                    raise ValidationError(
                        _("This application has already been processed.")
                    )
                if decision == "accept":
                    if not team.is_open or not application.role.available:
                        raise ValidationError(_("This role is no longer available."))
                    if team.memberships.filter(
                        user_id=application.applicant_id
                    ).exists():
                        raise ValidationError(_("This person is already in the team."))
                    Membership.objects.create(
                        team=team, user=application.applicant, role=application.role
                    )
                    application.status = "accepted"
                    chat, _created = Conversation.objects.get_or_create(team=team)
                    chat.participants.add(team.owner, application.applicant)
                    Application.objects.filter(
                        role__team=team,
                        applicant=application.applicant,
                        status="pending",
                    ).exclude(pk=pk).update(status="rejected")
                    if application.role.available == 0:
                        Application.objects.filter(
                            role=application.role, status="pending"
                        ).exclude(pk=pk).update(status="rejected")
                else:
                    application.status = "rejected"
                application.save(update_fields=["status"])
    except (ValidationError, IntegrityError) as e:
        messages.error(
            request,
            (
                e.messages[0]
                if isinstance(e, ValidationError)
                else _("This application has already been processed.")
            ),
        )
    else:
        messages.success(request, _("Saved successfully."))
    return redirect("applicants", pk=team.pk)


@login_required
@require_POST
def withdraw(request, pk):
    get_object_or_404(Application, pk=pk, applicant=request.user)
    Application.objects.filter(pk=pk, status="pending").update(status="withdrawn")
    return redirect("applications")


@login_required
@require_POST
def close_team(request, pk):
    team = get_object_or_404(Team, pk=pk, owner=request.user)
    with transaction.atomic():
        Team.objects.filter(pk=team.pk).update(is_open=False)
        Application.objects.filter(role__team=team, status="pending").update(
            status="rejected"
        )
    return redirect("team_detail", pk=pk)


@login_required
def applications(request):
    rows = Application.objects.filter(applicant=request.user).select_related(
        "role__team", "role__team__conversation"
    )
    return render(request, "community/applications.html", {"applications": rows})


@login_required
def my_teams(request):
    teams = (
        Team.objects.filter(Q(owner=request.user) | Q(memberships__user=request.user))
        .distinct()
        .select_related("owner")
        .prefetch_related("roles__memberships")
    )
    return render(request, "community/my_teams.html", {"teams": teams})


def person(request, pk):
    account = get_object_or_404(get_user_model(), pk=pk, is_active=True)
    profile = Profile.objects.filter(user=account).first()
    return render(
        request, "community/person.html", {"account": account, "profile": profile}
    )


@login_required
def resume(request, pk):
    profile = get_object_or_404(Profile, user_id=pk)
    allowed = (
        request.user.pk == pk
        or Application.objects.filter(
            applicant_id=pk,
            share_resume=True,
            status__in=["pending", "accepted"],
            role__team__owner=request.user,
        ).exists()
    )
    if not allowed:
        raise PermissionDenied
    if not profile.resume:
        raise PermissionDenied
    try:
        return FileResponse(
            profile.resume.open("rb"),
            as_attachment=True,
            filename="CV.pdf",
            content_type="application/pdf",
        )
    except FileNotFoundError:
        raise PermissionDenied


def learn(request):
    people = (
        get_user_model()
        .objects.filter(is_active=True, teaching_skills__isnull=False)
        .distinct()
    )
    q = request.GET.get("q", "").strip()[:150]
    skill = request.GET.get("skill", "")
    if q:
        people = people.filter(
            Q(username__icontains=q)
            | Q(profile__bio__icontains=q)
            | Q(teaching_skills__skill__name__icontains=q)
            | Q(teaching_skills__skill__name_ar__icontains=q)
        ).distinct()
    if skill.isdigit():
        people = people.filter(teaching_skills__skill_id=skill)
    if request.user.is_authenticated:
        people = people.exclude(pk=request.user.pk)
        wanted = Skill.objects.filter(
            interested_profiles__user=request.user
        ).values_list("pk", flat=True)
        people = people.annotate(
            match_count=Count(
                "teaching_skills", filter=Q(teaching_skills__skill_id__in=wanted)
            )
        ).order_by("-match_count", "username")
    else:
        people = people.order_by("username")
    people = people.select_related("profile").prefetch_related(
        "teaching_skills__skill", "profile__wanted_skills"
    )
    page = Paginator(people.distinct(), 9).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "community/learn.html",
        {
            "page_obj": page,
            "q": q,
            "skills": Skill.objects.all(),
            "selected_skill": skill,
            "filters": params.urlencode(),
        },
    )


@login_required
def teaching(request):
    form = TeachingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        try:
            with transaction.atomic():
                obj.save()
        except IntegrityError:
            form.add_error("skill", _("You already added this skill."))
        else:
            return redirect("teaching")
    return render(
        request,
        "community/teaching.html",
        {
            "form": form,
            "teaching": TeachingSkill.objects.filter(user=request.user).select_related(
                "skill"
            ),
        },
    )


@login_required
def learning_create(request, pk):
    teaching = get_object_or_404(
        TeachingSkill.objects.select_related("user", "skill"),
        pk=pk,
        user__is_active=True,
    )
    if teaching.user_id == request.user.pk:
        raise PermissionDenied
    form = LearningForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.sender = request.user
        obj.recipient = teaching.user
        obj.teaching = teaching
        try:
            with transaction.atomic():
                obj.save()
        except IntegrityError:
            form.add_error(None, _("An active request already exists for this skill."))
        else:
            messages.success(request, _("Your learning request has been sent."))
            return redirect("learning_requests")
    return render(
        request,
        "community/form.html",
        {
            "form": form,
            "heading": _("Connect and learn"),
            "intro": teaching.skill.display_name + " · " + teaching.user.username,
            "button": _("Send request"),
            "back": "/learn/",
        },
    )


@login_required
def learning_requests(request):
    requests = LearningRequest.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related(
        "sender", "recipient", "teaching__skill", "offered_skill__skill", "conversation"
    )
    return render(request, "community/requests.html", {"requests": requests})


@login_required
@require_POST
def learning_decide(request, pk, decision):
    obj = get_object_or_404(LearningRequest, pk=pk)
    if decision == "cancel":
        allowed = obj.sender_id == request.user.pk
    else:
        allowed = (
            decision in ["accept", "reject"] and obj.recipient_id == request.user.pk
        )
    if not allowed:
        raise PermissionDenied
    with transaction.atomic():
        status = {"accept": "accepted", "reject": "rejected", "cancel": "cancelled"}[
            decision
        ]
        updated = LearningRequest.objects.filter(pk=pk, status="pending").update(
            status=status
        )
        if updated and decision == "accept":
            chat = Conversation.objects.create(learning=obj)
            chat.participants.add(obj.sender, obj.recipient)
    return redirect("learning_requests")


@login_required
def inbox(request):
    chats = (
        request.user.conversations.select_related("team", "learning__teaching__skill")
        .annotate(latest=Max("messages__created_at"))
        .order_by("-latest", "-created_at")
    )
    return render(request, "community/inbox.html", {"chats": chats})


def authorized_chat(request, pk):
    chat = get_object_or_404(
        Conversation.objects.select_related("team", "learning__teaching__skill"),
        pk=pk,
        participants=request.user,
    )
    if chat.team_id:
        if (
            chat.team.owner_id != request.user.pk
            and not chat.team.memberships.filter(user=request.user).exists()
        ):
            raise PermissionDenied
    elif chat.learning.status != "accepted" or request.user.pk not in [
        chat.learning.sender_id,
        chat.learning.recipient_id,
    ]:
        raise PermissionDenied
    return chat


@login_required
def chat(request, pk):
    conversation = authorized_chat(request, pk)
    return render(
        request,
        "community/chat.html",
        {
            "chat": conversation,
            "chat_messages": list(
                conversation.messages.select_related("sender").order_by("-pk")[:100]
            )[::-1],
            "client_id": uuid.uuid4(),
        },
    )


@login_required
@require_GET
def chat_messages(request, pk):
    conversation = authorized_chat(request, pk)
    raw = request.GET.get("after", "0")
    if not raw.isdigit():
        return JsonResponse({"error": "Invalid cursor"}, status=400)
    rows = conversation.messages.filter(pk__gt=int(raw)).select_related("sender")[:100]
    return JsonResponse(
        {
            "messages": [
                {
                    "id": m.pk,
                    "sender": m.sender.username,
                    "mine": m.sender_id == request.user.pk,
                    "body": m.body,
                    "time": m.created_at.isoformat(),
                }
                for m in rows
            ]
        }
    )


@login_required
@require_POST
def chat_send(request, pk):
    conversation = authorized_chat(request, pk)
    body = request.POST.get("body", "").strip()
    try:
        client_id = uuid.UUID(request.POST.get("client_id", ""))
    except (ValueError, AttributeError):
        return JsonResponse(
            {"error": _("Invalid message. Please refresh.")}, status=400
        )
    if not body or len(body) > 2000:
        return JsonResponse(
            {"error": _("Write a message of 1 to 2000 characters.")}, status=400
        )
    try:
        with transaction.atomic():
            msg, created = Message.objects.get_or_create(
                client_id=client_id,
                defaults={
                    "conversation": conversation,
                    "sender": request.user,
                    "body": body,
                },
            )
            if (
                msg.conversation_id != conversation.pk
                or msg.sender_id != request.user.pk
            ):
                raise PermissionDenied
    except IntegrityError:
        return JsonResponse({"error": _("Please retry your message.")}, status=409)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"id": msg.pk})
    return redirect("chat", pk=pk)
