from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from community import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("accounts/", include("accounts.urls")),
    path("support/", include("support.urls")),
    path("", include("community.urls")),
]
handler404 = "config.views.page_not_found"
handler403 = "config.views.permission_denied"
handler500 = "config.views.server_error"
if settings.DEBUG:
    urlpatterns += static(
        "/media/avatars/", document_root=settings.MEDIA_ROOT / "avatars"
    )
