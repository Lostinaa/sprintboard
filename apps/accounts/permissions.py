"""
Custom permissions for role-based access control.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsManagerOrAdmin(BasePermission):
    """Allow access to managers and admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "manager")
        )


class IsOwnerOrReadOnly(BasePermission):
    """Object-level permission: only the owner can modify."""

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # Check common owner field names
        return getattr(obj, "owner", None) == request.user or getattr(
            obj, "user", None
        ) == request.user
