"""
URL routes for the projects app — nested resources.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "projects"

router = DefaultRouter()
router.register(r"projects", views.ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
    # Nested sprint routes
    path(
        "projects/<slug:project_slug>/sprints/",
        views.SprintViewSet.as_view({"get": "list", "post": "create"}),
        name="sprint-list",
    ),
    path(
        "projects/<slug:project_slug>/sprints/<uuid:pk>/",
        views.SprintViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="sprint-detail",
    ),
    path(
        "projects/<slug:project_slug>/sprints/<uuid:pk>/start/",
        views.SprintViewSet.as_view({"post": "start_sprint"}),
        name="sprint-start",
    ),
    path(
        "projects/<slug:project_slug>/sprints/<uuid:pk>/complete/",
        views.SprintViewSet.as_view({"post": "complete_sprint"}),
        name="sprint-complete",
    ),
    # Nested task routes
    path(
        "projects/<slug:project_slug>/tasks/",
        views.TaskViewSet.as_view({"get": "list", "post": "create"}),
        name="task-list",
    ),
    path(
        "projects/<slug:project_slug>/tasks/<uuid:pk>/",
        views.TaskViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="task-detail",
    ),
    path(
        "projects/<slug:project_slug>/tasks/<uuid:pk>/assign/",
        views.TaskViewSet.as_view({"post": "assign"}),
        name="task-assign",
    ),
    path(
        "projects/<slug:project_slug>/tasks/<uuid:pk>/transition/",
        views.TaskViewSet.as_view({"post": "transition"}),
        name="task-transition",
    ),
    # Nested comment routes
    path(
        "tasks/<uuid:task_pk>/comments/",
        views.CommentViewSet.as_view({"get": "list", "post": "create"}),
        name="comment-list",
    ),
    path(
        "tasks/<uuid:task_pk>/comments/<uuid:pk>/",
        views.CommentViewSet.as_view({"delete": "destroy"}),
        name="comment-detail",
    ),
    # Activity log
    path(
        "tasks/<uuid:task_pk>/activity/",
        views.ActivityLogView.as_view(),
        name="activity-log",
    ),
]
