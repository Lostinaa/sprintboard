"""
Tests for the User model.
"""

import pytest
from django.contrib.auth import get_user_model

from .factories import AdminFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="securepassword123",
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "test@example.com"
        assert user.check_password("securepassword123")
        assert user.role == "developer"
        assert user.is_active is True
        assert user.is_staff is False

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            first_name="Admin",
            last_name="User",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == "admin"

    def test_email_is_required(self):
        with pytest.raises(ValueError, match="Email address is required"):
            User.objects.create_user(email="", password="pass123")

    def test_full_name_property(self):
        user = UserFactory(first_name="Jane", last_name="Smith")
        assert user.full_name == "Jane Smith"

    def test_user_str(self):
        user = UserFactory(email="display@test.com")
        assert str(user) == "display@test.com"

    def test_uuid_primary_key(self):
        user = UserFactory()
        assert user.pk is not None
        assert len(str(user.pk)) == 36  # UUID format

    def test_factory_creates_valid_user(self):
        user = UserFactory()
        assert user.is_active is True
        assert user.role == "developer"

    def test_admin_factory(self):
        admin = AdminFactory()
        assert admin.role == "admin"
        assert admin.is_staff is True
        assert admin.is_superuser is True
