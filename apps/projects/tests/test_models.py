"""
Tests for project domain models.
"""

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory

from .factories import ProjectFactory, SprintFactory, TaskFactory


@pytest.mark.django_db
class TestProjectModel:
    def test_create_project(self):
        project = ProjectFactory(name="Test Project", slug="test-project")
        assert project.name == "Test Project"
        assert project.slug == "test-project"
        assert project.is_archived is False

    def test_project_str(self):
        project = ProjectFactory(name="My App")
        assert str(project) == "My App"

    def test_active_sprint_returns_active(self):
        project = ProjectFactory()
        SprintFactory(project=project, status="planning")
        active = SprintFactory(project=project, status="active")
        assert project.active_sprint == active

    def test_active_sprint_returns_none_when_no_active(self):
        project = ProjectFactory()
        SprintFactory(project=project, status="planning")
        assert project.active_sprint is None


@pytest.mark.django_db
class TestSprintModel:
    def test_sprint_str(self):
        sprint = SprintFactory()
        assert sprint.project.name in str(sprint)

    def test_is_overdue_when_past_end_date(self):
        sprint = SprintFactory(
            status="active",
            end_date=timezone.now().date() - timezone.timedelta(days=1),
        )
        assert sprint.is_overdue is True

    def test_is_not_overdue_when_within_dates(self):
        sprint = SprintFactory(
            status="active",
            end_date=timezone.now().date() + timezone.timedelta(days=5),
        )
        assert sprint.is_overdue is False

    def test_velocity_sums_completed_points(self):
        sprint = SprintFactory()
        TaskFactory(sprint=sprint, project=sprint.project, status="done", story_points=5)
        TaskFactory(sprint=sprint, project=sprint.project, status="done", story_points=3)
        TaskFactory(sprint=sprint, project=sprint.project, status="in_progress", story_points=8)
        assert sprint.velocity == 8


@pytest.mark.django_db
class TestTaskModel:
    def test_task_str(self):
        task = TaskFactory(title="Fix login bug")
        assert str(task) == "Fix login bug"

    def test_is_overdue(self):
        task = TaskFactory(
            status="in_progress",
            due_date=timezone.now().date() - timezone.timedelta(days=1),
        )
        assert task.is_overdue is True

    def test_done_task_not_overdue(self):
        task = TaskFactory(
            status="done",
            due_date=timezone.now().date() - timezone.timedelta(days=1),
        )
        assert task.is_overdue is False

    def test_mark_done(self):
        task = TaskFactory(status="in_progress")
        task.mark_done()
        task.refresh_from_db()
        assert task.status == "done"
        assert task.completed_at is not None

    def test_default_priority_is_medium(self):
        task = TaskFactory()
        assert task.priority == "medium"

    def test_labels_default_to_empty_list(self):
        task = TaskFactory()
        assert task.labels == []


@pytest.mark.django_db
class TestActivityLogSignal:
    def test_activity_log_created_on_task_creation(self):
        task = TaskFactory()
        assert task.activity_logs.filter(action="created").exists()

    def test_activity_log_on_status_change(self):
        task = TaskFactory(status="todo")
        task.status = "in_progress"
        task.save()
        assert task.activity_logs.filter(
            action="status_changed",
        ).exists()
