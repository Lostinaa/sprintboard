"""
Admin configuration for the projects app.
"""

from django.contrib import admin

from .models import ActivityLog, Comment, Project, ProjectMembership, Sprint, Task


class MembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0
    raw_id_fields = ("user",)


class SprintInline(admin.TabularInline):
    model = Sprint
    extra = 0
    fields = ("name", "status", "start_date", "end_date")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "is_archived", "created_at")
    list_filter = ("is_archived", "created_at")
    search_fields = ("name", "slug", "owner__email")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("owner",)
    inlines = [MembershipInline, SprintInline]


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "status", "start_date", "end_date")
    list_filter = ("status",)
    search_fields = ("name", "project__name")
    raw_id_fields = ("project",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "assignee", "due_date")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description")
    raw_id_fields = ("project", "sprint", "assignee", "reporter")
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    raw_id_fields = ("task", "author")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "action", "created_at")
    list_filter = ("action",)
    raw_id_fields = ("task", "user")
    readonly_fields = ("task", "user", "action", "detail", "created_at")
