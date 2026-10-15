from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "user",
        "category",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "category",
        "created_at",
    )

    search_fields = (
        "subject",
        "message",
        "user__username",
    )

    list_select_related = ("user",)

    readonly_fields = (
        "user",
        "category",
        "subject",
        "message",
        "created_at",
        "updated_at",
    )

    fields = (
        "user",
        "category",
        "subject",
        "message",
        "status",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
