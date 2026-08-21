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
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        # Без этой проверки уволенный (is_active=False) сотрудник с уже
        # открытой сессией сохранял полный доступ до истечения сессии —
        # authenticate() проверяет is_active только при самом логине,
        # а get_user() вызывается на КАЖДЫЙ запрос уже залогиненного
        # пользователя и раньше эту проверку не повторял (аудит, п. 2.1).
        if not user.is_active:
            return None
        return user
