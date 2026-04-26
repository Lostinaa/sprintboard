"""
Factories for generating test data — projects app.
"""

import factory
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory

from ..models import Comment, Project, Sprint, Task


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    description = factory.Faker("paragraph")
    owner = factory.SubFactory(UserFactory)


class SprintFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sprint

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Sprint {n}")
    goal = factory.Faker("sentence")
    status = Sprint.Status.PLANNING
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(
        lambda: timezone.now().date() + timezone.timedelta(days=14)
    )


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    project = factory.SubFactory(ProjectFactory)
    title = factory.Faker("sentence", nb_words=5)
    description = factory.Faker("paragraph")
    status = Task.Status.TODO
    priority = Task.Priority.MEDIUM
    story_points = factory.Faker("random_int", min=1, max=13)
    reporter = factory.SubFactory(UserFactory)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    body = factory.Faker("paragraph")
