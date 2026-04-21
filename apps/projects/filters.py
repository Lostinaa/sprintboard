"""
django-filter FilterSets for projects app.
"""

import django_filters

from .models import Task


class TaskFilter(django_filters.FilterSet):
    """Advanced filtering for tasks."""

    status = django_filters.ChoiceFilter(choices=Task.Status.choices)
    priority = django_filters.ChoiceFilter(choices=Task.Priority.choices)
    assignee = django_filters.UUIDFilter(field_name="assignee__id")
    sprint = django_filters.UUIDFilter(field_name="sprint__id")
    is_unassigned = django_filters.BooleanFilter(
        field_name="assignee", lookup_expr="isnull"
    )
    due_before = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")
    due_after = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    label = django_filters.CharFilter(method="filter_by_label")

    class Meta:
        model = Task
        fields = [
            "status",
            "priority",
            "assignee",
            "sprint",
            "is_unassigned",
            "due_before",
            "due_after",
        ]

    def filter_by_label(self, queryset, name, value):
        """Filter tasks that contain a specific label in their JSON labels array."""
        return queryset.filter(labels__contains=[value])
