"""
Tests for project API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory

from .factories import ProjectFactory, SprintFactory, TaskFactory


@pytest.mark.django_db
class TestProjectViewSet:
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_create_project(self):
        url = reverse("projects:project-list")
        payload = {
            "name": "New Project",
            "slug": "new-project",
            "description": "A test project",
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Project"
        assert str(response.data["owner"]) == str(self.user.id)

    def test_list_only_own_projects(self):
        ProjectFactory(owner=self.user)
        ProjectFactory()  # another user's project
        url = reverse("projects:project-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_retrieve_project(self):
        project = ProjectFactory(owner=self.user)
        url = reverse("projects:project-detail", kwargs={"slug": project.slug})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == project.slug


@pytest.mark.django_db
class TestSprintEndpoints:
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.project = ProjectFactory(owner=self.user)

    def test_create_sprint(self):
        url = reverse("projects:sprint-list", kwargs={"project_slug": self.project.slug})
        payload = {
            "project": str(self.project.id),
            "name": "Sprint 1",
            "goal": "Set up foundation",
            "start_date": "2026-05-01",
            "end_date": "2026-05-14",
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Sprint 1"

    def test_start_sprint(self):
        sprint = SprintFactory(project=self.project, status="planning")
        url = reverse(
            "projects:sprint-start",
            kwargs={"project_slug": self.project.slug, "pk": sprint.pk},
        )
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "active"


@pytest.mark.django_db
class TestTaskEndpoints:
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.project = ProjectFactory(owner=self.user)

    def test_create_task(self):
        url = reverse("projects:task-list", kwargs={"project_slug": self.project.slug})
        payload = {
            "project": str(self.project.id),
            "title": "Implement login",
            "description": "JWT-based auth",
            "priority": "high",
            "story_points": 5,
        }
        response = self.client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["reporter"]) == str(self.user.id)

    def test_transition_task(self):
        task = TaskFactory(project=self.project, status="todo")
        url = reverse(
            "projects:task-transition",
            kwargs={"project_slug": self.project.slug, "pk": task.pk},
        )
        response = self.client.post(url, {"status": "in_progress"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "in_progress"

    def test_invalid_transition(self):
        task = TaskFactory(project=self.project)
        url = reverse(
            "projects:task-transition",
            kwargs={"project_slug": self.project.slug, "pk": task.pk},
        )
        response = self.client.post(url, {"status": "invalid_status"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_tasks_by_status(self):
        TaskFactory(project=self.project, status="todo")
        TaskFactory(project=self.project, status="done")
        url = reverse("projects:task-list", kwargs={"project_slug": self.project.slug})
        response = self.client.get(url, {"status": "todo"})
        assert response.status_code == status.HTTP_200_OK
        assert all(t["status"] == "todo" for t in response.data["results"])
