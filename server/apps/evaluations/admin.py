from django.contrib import admin

from .models import Deliverable, ProjectAssignment


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "project", "due_date", "status", "created_at")
    list_filter = ("status", "project")


@admin.register(Deliverable)
class DeliverableAdmin(admin.ModelAdmin):
    list_display = ("assignment", "repository_url", "score", "status", "reviewed_by", "submitted_at")
    list_filter = ("status",)
    search_fields = ("repository_url", "feedback")
