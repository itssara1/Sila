from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import ProfileForm, SignUpForm
from .models import Profile


from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import resolve_url
from django.utils.translation import gettext as _


class SilaLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["login_form"] = context["form"]
        context["signup_form"] = SignUpForm(
            auto_id="signup_%s",
        )
        context["auth_mode"] = "login"

        return context


def signup(request):
    next_url = request.POST.get(
        "next",
        request.GET.get("next", ""),
    )

    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ""

    destination = next_url or resolve_url(settings.LOGIN_REDIRECT_URL)

    if request.user.is_authenticated:
        return redirect(destination)

    if request.method == "POST":
        form = SignUpForm(
            request.POST,
            auto_id="signup_%s",
        )

        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                Profile.objects.get_or_create(user=user)

            login(request, user)
            return redirect(destination)
    else:
        form = SignUpForm(
            auto_id="signup_%s",
        )

    return render(
        request,
        "accounts/signup.html",
        {
            "form": form,
            "signup_form": form,
            "login_form": AuthenticationForm(request=request),
            "auth_mode": "signup",
            "next": next_url,
        },
    )


@login_required
def profile_update(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("Your profile has been updated."),
            )

            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )
