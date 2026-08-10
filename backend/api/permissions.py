"""Permission-классы для ролевой авторизации."""
from rest_framework.permissions import BasePermission


def _has_role(user, roles: set[str]) -> bool:
    return bool(user and user.is_authenticated and user.has_role(*roles))


class IsHR(BasePermission):
    message = "Только для HR"

    def has_permission(self, request, view) -> bool:
        return _has_role(request.user, {"HR"})


class IsHROrManager(BasePermission):
    message = "Только для HR и Manager"

    def has_permission(self, request, view) -> bool:
        return _has_role(request.user, {"HR", "Manager"})
