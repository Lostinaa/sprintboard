"""
Views for the projects app — ViewSets with proper permissions.
"""

from django.db.models import Count, Q, Sum
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAdmin

from .filters import TaskFilter
from .models import ActivityLog, Comment, Project, ProjectMembership, Sprint, Task
from .serializers import (
    ActivityLogSerializer,
    CommentSerializer,
    MembershipSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    SprintSerializer,
    TaskSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for projects.
    - List/Create: any authenticated user
    - Retrieve/Update/Delete: owner or project members
    """

    lookup_field = "slug"

    def get_queryset(self):
        qs = Project.objects.select_related("owner").prefetch_related("memberships")
        if self.action == "list":
            # Show projects the user owns or is a member of
            return qs.filter(
                Q(owner=self.request.user) | Q(members=self.request.user)
            ).distinct()
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        # Auto-add owner as lead member
        ProjectMembership.objects.create(
            user=self.request.user,
            project=project,
            role=ProjectMembership.ProjectRole.LEAD,
        )

    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, slug=None):
        """Add a member to the project."""
        project = self.get_object()
        user_id = request.data.get("user_id")
        role = request.data.get("role", "member")

        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership, created = ProjectMembership.objects.get_or_create(
            project=project,
            user_id=user_id,
            defaults={"role": role},
        )

        if not created:
            return Response(
                {"detail": "User is already a member."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="dashboard")
    def dashboard(self, request, slug=None):
        """Project dashboard — aggregated metrics."""
        project = self.get_object()

        task_stats = (
            project.tasks.values("status")
            .annotate(count=Count("id"), points=Sum("story_points"))
            .order_by("status")
        )

        active_sprint = project.active_sprint
        overdue_count = project.tasks.filter(
            due_date__lt="now", status__in=["backlog", "todo", "in_progress", "in_review"]
        ).count()

        return Response(
            {
                "project": ProjectListSerializer(project).data,
                "task_stats": list(task_stats),
                "active_sprint": SprintSerializer(active_sprint).data if active_sprint else None,
                "overdue_tasks": overdue_count,
                "total_members": project.memberships.count(),
            }
        )


class SprintViewSet(viewsets.ModelViewSet):
    """CRUD for sprints within a project."""

    serializer_class = SprintSerializer

    def get_queryset(self):
        return Sprint.objects.filter(
            project__slug=self.kwargs["project_slug"]
        ).select_related("project")

    def perform_create(self, serializer):
        project = Project.objects.get(slug=self.kwargs["project_slug"])
        serializer.save(project=project)

    @action(detail=True, methods=["post"], url_path="start")
    def start_sprint(self, request, project_slug=None, pk=None):
        """Activate a sprint (only one active sprint per project)."""
        sprint = self.get_object()

        # Deactivate any currently active sprint
        Sprint.objects.filter(
            project=sprint.project, status=Sprint.Status.ACTIVE
        ).update(status=Sprint.Status.COMPLETED)

        sprint.status = Sprint.Status.ACTIVE
        sprint.save(update_fields=["status", "updated_at"])
        return Response(SprintSerializer(sprint).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete_sprint(self, request, project_slug=None, pk=None):
        """Complete a sprint and move unfinished tasks to backlog."""
        sprint = self.get_object()
        sprint.status = Sprint.Status.COMPLETED
        sprint.save(update_fields=["status", "updated_at"])

        # Move incomplete tasks back to backlog
        incomplete = sprint.tasks.exclude(status=Task.Status.DONE)
        moved_count = incomplete.update(sprint=None, status=Task.Status.BACKLOG)

        return Response(
            {
                "sprint": SprintSerializer(sprint).data,
                "tasks_moved_to_backlog": moved_count,
            }
        )


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD for tasks — supports filtering, search, ordering."""

    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["priority", "created_at", "due_date", "story_points"]

    def get_queryset(self):
        return (
            Task.objects.filter(project__slug=self.kwargs["project_slug"])
            .select_related("assignee", "reporter", "sprint")
            .prefetch_related("comments")
        )

    def perform_create(self, serializer):
        project = Project.objects.get(slug=self.kwargs["project_slug"])
        serializer.save(project=project, reporter=self.request.user)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, project_slug=None, pk=None):
        """Assign a task to a user."""
        task = self.get_object()
        user_id = request.data.get("assignee_id")
        task.assignee_id = user_id
        task.save(update_fields=["assignee", "updated_at"])

        ActivityLog.objects.create(
            task=task,
            user=request.user,
            action=ActivityLog.Action.ASSIGNED,
            detail={"assignee_id": str(user_id)},
        )

        return Response(TaskSerializer(task).data)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, project_slug=None, pk=None):
        """Change task status with validation."""
        task = self.get_object()
        new_status = request.data.get("status")

        valid_statuses = [s[0] for s in Task.Status.choices]
        if new_status not in valid_statuses:
            return Response(
                {"detail": f"Invalid status. Must be one of: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = new_status
        if new_status == Task.Status.DONE:
            from django.utils import timezone
            task.completed_at = timezone.now()

        task.save(update_fields=["status", "completed_at", "updated_at"])
        return Response(TaskSerializer(task).data)


class CommentViewSet(viewsets.ModelViewSet):
    """Comments on a specific task."""

    serializer_class = CommentSerializer
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return Comment.objects.filter(
            task_id=self.kwargs["task_pk"]
        ).select_related("author")

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            task_id=self.kwargs["task_pk"],
        )


class ActivityLogView(generics.ListAPIView):
    """Read-only activity feed for a task."""

    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        return ActivityLog.objects.filter(
            task_id=self.kwargs["task_pk"]
        ).select_related("user")
