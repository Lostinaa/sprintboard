"""
Project & Sprint models — core domain entities.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(TimeStampedModel):
    """A project groups sprints and tasks under a single product."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectMembership",
        related_name="projects",
    )
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return self.name

    @property
    def active_sprint(self):
        """Return the currently active sprint, if any."""
        return self.sprints.filter(status=Sprint.Status.ACTIVE).first()

    @property
    def task_summary(self):
        """Return a dict of task counts by status."""
        from django.db.models import Count

        return dict(
            self.tasks.values_list("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )


class ProjectMembership(TimeStampedModel):
    """Through model — tracks when users joined and their project role."""

    class ProjectRole(models.TextChoices):
        LEAD = "lead", "Lead"
        MEMBER = "member", "Member"
        VIEWER = "viewer", "Viewer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20, choices=ProjectRole.choices, default=ProjectRole.MEMBER
    )

    class Meta:
        unique_together = ("user", "project")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} → {self.project.name} ({self.role})"


class Sprint(TimeStampedModel):
    """A time-boxed iteration within a project."""

    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="sprints"
    )
    name = models.CharField(max_length=200)
    goal = models.TextField(blank=True, help_text="Sprint goal / objective")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNING
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self):
        return f"{self.project.name} — {self.name}"

    @property
    def is_overdue(self):
        return (
            self.status == self.Status.ACTIVE
            and self.end_date
            and self.end_date < timezone.now().date()
        )

    @property
    def velocity(self):
        """Story points completed in this sprint."""
        return (
            self.tasks.filter(status=Task.Status.DONE).aggregate(
                total=models.Sum("story_points")
            )["total"]
            or 0
        )


class Task(TimeStampedModel):
    """A work item within a project, optionally tied to a sprint."""

    class Status(models.TextChoices):
        BACKLOG = "backlog", "Backlog"
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        IN_REVIEW = "in_review", "In Review"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks"
    )
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.BACKLOG
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    story_points = models.PositiveSmallIntegerField(null=True, blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    labels = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["sprint"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return (
            self.status not in (self.Status.DONE,)
            and self.due_date
            and self.due_date < timezone.now().date()
        )

    def mark_done(self):
        """Transition task to done and record completion time."""
        self.status = self.Status.DONE
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])


class Comment(TimeStampedModel):
    """Discussion thread on a task."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on {self.task.title[:30]}"


class ActivityLog(TimeStampedModel):
    """Audit trail for task changes."""

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        STATUS_CHANGED = "status_changed", "Status Changed"
        ASSIGNED = "assigned", "Assigned"
        COMMENTED = "commented", "Commented"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="activity_logs"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    detail = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} — {self.task.title[:30]}"
