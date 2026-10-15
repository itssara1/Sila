from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile, User

admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "bio")
    search_fields = ("user__username", "bio")
    filter_horizontal = ("wanted_skills",)
