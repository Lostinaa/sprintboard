"""
Tests for account API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .factories import AdminFactory, UserFactory


@pytest.mark.django_db
class TestRegisterView:
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("accounts:register")

    def test_register_success(self):
        payload = {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "strongpass123",
            "password_confirm": "strongpass123",
        }
        response = self.client.post(self.url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert "tokens" in response.data
        assert response.data["user"]["email"] == "new@example.com"

    def test_register_password_mismatch(self):
        payload = {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "strongpass123",
            "password_confirm": "differentpass",
        }
        response = self.client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self):
        UserFactory(email="existing@example.com")
        payload = {
            "email": "existing@example.com",
            "first_name": "Dup",
            "last_name": "User",
            "password": "strongpass123",
            "password_confirm": "strongpass123",
        }
        response = self.client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginView:
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("accounts:login")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email="login@test.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_login_success(self):
        response = self.client.post(
            self.url, {"email": "login@test.com", "password": "testpass123"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self):
        response = self.client.post(
            self.url, {"email": "login@test.com", "password": "wrong"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfileView:
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory(first_name="Profile", last_name="Test")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("accounts:profile")

    def test_get_profile(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == self.user.email

    def test_update_profile(self):
        response = self.client.patch(self.url, {"bio": "Updated bio text"})
        assert response.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.bio == "Updated bio text"

    def test_unauthenticated_access(self):
        client = APIClient()
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserListView:
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("accounts:user-list")

    def test_admin_can_list_users(self):
        admin = AdminFactory()
        self.client.force_authenticate(user=admin)
        UserFactory.create_batch(3)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 3

    def test_non_admin_cannot_list_users(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
