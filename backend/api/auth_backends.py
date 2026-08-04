"""Кастомный auth backend: логин по email + проверка BCrypt."""
from django.contrib.auth.backends import BaseBackend

from .models import User


class EmailBackend(BaseBackend):
    def authenticate(self, request, email: str | None = None, password: str | None = None, **kwargs):
        if not email or not password:
            return None
        try:
            user = User.objects.get(email__iexact=email.strip())
        except User.DoesNotExist:
            return None
        if user.is_active and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
