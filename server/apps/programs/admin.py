from django.contrib import admin
from .models import Program, Project


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description")
    ordering = ("-created_at",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "program", "order", "duration_days", "status", "created_at")
    list_filter = ("status", "program")
    search_fields = ("title", "description")
    ordering = ("program", "order")

