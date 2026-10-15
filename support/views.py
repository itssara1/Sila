from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from .forms import FeedbackForm


@login_required
@require_http_methods(["GET", "POST"])
def contact(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)

        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()

            messages.success(
                request,
                _(
                    "Your message has been received. Thank you for helping us improve Sila."
                ),
            )

            return redirect("support:contact")
    else:
        form = FeedbackForm()

    return render(
        request,
        "support/contact.html",
        {"form": form},
    )
