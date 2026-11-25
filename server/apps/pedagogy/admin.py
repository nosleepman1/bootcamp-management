from django.contrib import admin

from .models import Absence, CourseSession


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "cohort", "project", "trainer", "session_date", "status")
    list_filter = ("status", "session_date", "cohort")
    search_fields = ("title", "description")


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ("course_session", "enrollment", "is_absent", "is_justified", "created_at")
    list_filter = ("is_absent", "is_justified")
    search_fields = ("reason", "enrollment__user__email")
