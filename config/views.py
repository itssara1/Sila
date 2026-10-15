from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template.loader import render_to_string


def page_not_found(request, exception):
    return render(request, "errors/404.html", status=404)


def permission_denied(request, exception):
    return render(request, "errors/403.html", status=403)


def server_error(request):
    html = render_to_string("errors/500.html")
    return HttpResponseServerError(html)


def csrf_failure(request, reason=""):
    return render(request, "errors/csrf.html", status=403)
