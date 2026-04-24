"""
Signals — auto-create activity logs on task events.
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import ActivityLog, Comment, Task

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Task)
def capture_task_status_change(sender, instance, **kwargs):
    """Track status transitions before save."""
    if instance.pk:
        try:
            old = Task.objects.get(pk=instance.pk)
            if old.status != instance.status:
                # Stash old status for post_save to create the log
                instance._old_status = old.status
        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=Task)
def log_task_activity(sender, instance, created, **kwargs):
    """Create an activity log entry when a task is created or status changes."""
    if created:
        ActivityLog.objects.create(
            task=instance,
            user=instance.reporter,
            action=ActivityLog.Action.CREATED,
            detail={"status": instance.status},
        )
        logger.info("Task created: %s", instance.title)
    elif hasattr(instance, "_old_status"):
        ActivityLog.objects.create(
            task=instance,
            user=instance.assignee,
            action=ActivityLog.Action.STATUS_CHANGED,
            detail={
                "from": instance._old_status,
                "to": instance.status,
            },
        )
        logger.info(
            "Task %s: %s → %s",
            instance.title,
            instance._old_status,
            instance.status,
        )
        del instance._old_status


@receiver(post_save, sender=Comment)
def log_comment_activity(sender, instance, created, **kwargs):
    """Log when a comment is added to a task."""
    if created:
        ActivityLog.objects.create(
            task=instance.task,
            user=instance.author,
            action=ActivityLog.Action.COMMENTED,
            detail={"comment_id": str(instance.id)},
        )
