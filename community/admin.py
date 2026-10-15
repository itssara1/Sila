from django.contrib import admin
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


# Workflow records are read-only here so accepting requests always runs through application rules.
class WorkflowAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in [
    Team,
    Role,
    Application,
    Membership,
    TeachingSkill,
    LearningRequest,
    Conversation,
    Message,
]:
    admin.site.register(model, WorkflowAdmin)
