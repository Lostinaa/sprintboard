"""
Celery tasks for the projects app.
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def flag_overdue_tasks():
    """
    Periodic task: find tasks past their due date that aren't done
    and add an 'overdue' label.
    """
    from .models import Task

    today = timezone.now().date()
    overdue_tasks = Task.objects.filter(
        due_date__lt=today,
        status__in=[
            Task.Status.BACKLOG,
            Task.Status.TODO,
            Task.Status.IN_PROGRESS,
            Task.Status.IN_REVIEW,
        ],
    ).exclude(labels__contains=["overdue"])

    count = 0
    for task in overdue_tasks:
        if "overdue" not in task.labels:
            task.labels.append("overdue")
            task.save(update_fields=["labels", "updated_at"])
            count += 1

    logger.info("Flagged %d overdue tasks", count)
    return {"flagged": count}


@shared_task
def send_assignment_notification(task_id, assignee_id):
    """
    Async task: send notification when a task is assigned.
    In production, this would integrate with email/Slack.
    """
    from django.contrib.auth import get_user_model

    from .models import Task

    User = get_user_model()

    try:
        task = Task.objects.select_related("project").get(id=task_id)
        user = User.objects.get(id=assignee_id)
        logger.info(
            "Notification: %s assigned to '%s' in project '%s'",
            user.email,
            task.title,
            task.project.name,
        )
        # TODO: Integrate with email service or Slack webhook
        return {"sent_to": user.email, "task": task.title}
    except (Task.DoesNotExist, User.DoesNotExist) as e:
        logger.error("Notification failed: %s", str(e))
        return {"error": str(e)}
