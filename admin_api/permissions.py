from rest_framework.permissions import BasePermission


class IsAdminStaff(BasePermission):
    """Allow access only to authenticated staff/admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
