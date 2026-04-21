"""
Serializers for the projects app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ActivityLog, Comment, Project, ProjectMembership, Sprint, Task

User = get_user_model()


class MembershipSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="user.email")
    full_name = serializers.ReadOnlyField(source="user.full_name")

    class Meta:
        model = ProjectMembership
        fields = ["id", "user", "email", "full_name", "role", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    owner_name = serializers.ReadOnlyField(source="owner.full_name")
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "owner",
            "owner_name",
            "member_count",
            "task_count",
            "is_archived",
            "created_at",
        ]
        read_only_fields = ["id", "owner", "created_at"]

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_task_count(self, obj):
        return obj.tasks.count()


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Full project detail with nested sprints and membership info."""

    owner_name = serializers.ReadOnlyField(source="owner.full_name")
    memberships = MembershipSerializer(many=True, read_only=True)
    active_sprint = serializers.SerializerMethodField()
    task_summary = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "owner",
            "owner_name",
            "memberships",
            "active_sprint",
            "task_summary",
            "is_archived",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_active_sprint(self, obj):
        sprint = obj.active_sprint
        if sprint:
            return SprintSerializer(sprint).data
        return None


class SprintSerializer(serializers.ModelSerializer):
    velocity = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = [
            "id",
            "project",
            "name",
            "goal",
            "status",
            "start_date",
            "end_date",
            "velocity",
            "is_overdue",
            "task_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_task_count(self, obj):
        return obj.tasks.count()

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.ReadOnlyField(source="assignee.full_name")
    reporter_name = serializers.ReadOnlyField(source="reporter.full_name")
    is_overdue = serializers.ReadOnlyField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "sprint",
            "title",
            "description",
            "status",
            "priority",
            "story_points",
            "assignee",
            "assignee_name",
            "reporter",
            "reporter_name",
            "due_date",
            "completed_at",
            "labels",
            "is_overdue",
            "comment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reporter", "completed_at", "created_at", "updated_at"]

    def get_comment_count(self, obj):
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source="author.full_name")
    author_email = serializers.ReadOnlyField(source="author.email")

    class Meta:
        model = Comment
        fields = ["id", "task", "author", "author_name", "author_email", "body", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = ActivityLog
        fields = ["id", "task", "user", "user_email", "action", "detail", "created_at"]
        read_only_fields = "__all__"
