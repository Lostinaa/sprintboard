"""
Factories for generating test data — accounts app.
"""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@sprintboard.io")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = "developer"
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True


class AdminFactory(UserFactory):
    email = factory.Sequence(lambda n: f"admin{n}@sprintboard.io")
    role = "admin"
    is_staff = True
    is_superuser = True


class ManagerFactory(UserFactory):
    email = factory.Sequence(lambda n: f"manager{n}@sprintboard.io")
    role = "manager"
