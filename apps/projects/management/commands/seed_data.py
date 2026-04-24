"""
Management command to seed the database with sample data.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.tests.factories import ManagerFactory, UserFactory
from apps.projects.models import Comment, Project, ProjectMembership, Sprint, Task


class Command(BaseCommand):
    help = "Seed the database with sample projects, sprints, and tasks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Task.objects.all().delete()
            Sprint.objects.all().delete()
            Project.objects.all().delete()

        self.stdout.write("Creating users...")
        manager = ManagerFactory(
            email="sarah@sprintboard.io",
            first_name="Sarah",
            last_name="Chen",
        )
        dev1 = UserFactory(
            email="alex@sprintboard.io",
            first_name="Alex",
            last_name="Rivera",
        )
        dev2 = UserFactory(
            email="maya@sprintboard.io",
            first_name="Maya",
            last_name="Patel",
        )

        self.stdout.write("Creating project...")
        project = Project.objects.create(
            name="SprintBoard Platform",
            slug="sprintboard-platform",
            description="Internal project management tool built with Django + DRF",
            owner=manager,
        )

        for user, role in [(manager, "lead"), (dev1, "member"), (dev2, "member")]:
            ProjectMembership.objects.create(user=user, project=project, role=role)

        self.stdout.write("Creating sprints...")
        completed_sprint = Sprint.objects.create(
            project=project,
            name="Sprint 1 — Foundation",
            goal="Set up project structure, auth, and CI/CD",
            status=Sprint.Status.COMPLETED,
            start_date=timezone.now().date() - timezone.timedelta(days=21),
            end_date=timezone.now().date() - timezone.timedelta(days=7),
        )

        active_sprint = Sprint.objects.create(
            project=project,
            name="Sprint 2 — Core Features",
            goal="Implement task management, comments, and activity feed",
            status=Sprint.Status.ACTIVE,
            start_date=timezone.now().date() - timezone.timedelta(days=7),
            end_date=timezone.now().date() + timezone.timedelta(days=7),
        )

        self.stdout.write("Creating tasks...")
        tasks_data = [
            # Completed sprint tasks
            {"title": "Set up Django project structure", "status": "done", "sprint": completed_sprint, "assignee": dev1, "priority": "high", "story_points": 3},
            {"title": "Implement JWT authentication", "status": "done", "sprint": completed_sprint, "assignee": dev1, "priority": "critical", "story_points": 5},
            {"title": "Configure PostgreSQL + Docker", "status": "done", "sprint": completed_sprint, "assignee": dev2, "priority": "high", "story_points": 3},
            {"title": "Write user model tests", "status": "done", "sprint": completed_sprint, "assignee": dev2, "priority": "medium", "story_points": 2},
            # Active sprint tasks
            {"title": "Build project CRUD API", "status": "done", "sprint": active_sprint, "assignee": dev1, "priority": "high", "story_points": 5},
            {"title": "Implement task filtering & search", "status": "in_progress", "sprint": active_sprint, "assignee": dev2, "priority": "high", "story_points": 5},
            {"title": "Add comment system", "status": "in_progress", "sprint": active_sprint, "assignee": dev1, "priority": "medium", "story_points": 3},
            {"title": "Create activity log signals", "status": "todo", "sprint": active_sprint, "assignee": dev2, "priority": "medium", "story_points": 3},
            {"title": "Sprint dashboard endpoint", "status": "todo", "sprint": active_sprint, "assignee": None, "priority": "medium", "story_points": 5},
            # Backlog
            {"title": "WebSocket real-time notifications", "status": "backlog", "sprint": None, "assignee": None, "priority": "low", "story_points": 8},
            {"title": "File attachments on tasks", "status": "backlog", "sprint": None, "assignee": None, "priority": "low", "story_points": 5},
            {"title": "Burndown chart API endpoint", "status": "backlog", "sprint": None, "assignee": None, "priority": "medium", "story_points": 5},
        ]

        for td in tasks_data:
            task = Task.objects.create(
                project=project,
                reporter=manager,
                due_date=timezone.now().date() + timezone.timedelta(days=7),
                **td,
            )
            if td["status"] == "done":
                task.completed_at = timezone.now()
                task.save(update_fields=["completed_at"])

        # Add some comments
        task_with_comments = Task.objects.filter(title__icontains="filtering").first()
        if task_with_comments:
            Comment.objects.create(
                task=task_with_comments,
                author=manager,
                body="Make sure we support filtering by label using the JSON field.",
            )
            Comment.objects.create(
                task=task_with_comments,
                author=dev2,
                body="Done — using `labels__contains` for Postgres JSON lookup.",
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: 3 users, 1 project, 2 sprints, {len(tasks_data)} tasks"
            )
        )
