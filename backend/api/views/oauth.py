import json
import secrets
import urllib.parse
import urllib.request
import uuid
from urllib.error import URLError

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import User
from ..serializers import UserPublicSerializer, issue_tokens_for_user

YANDEX_AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USERINFO_URL = "https://login.yandex.ru/info"


TICKET_TTL_SECONDS = 60
STATE_TTL_SECONDS = 600


def _yandex_config_ok() -> bool:
    return bool(
        getattr(settings, "YANDEX_CLIENT_ID", "")
        and getattr(settings, "YANDEX_CLIENT_SECRET", "")
    )


class YandexStartView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        if not _yandex_config_ok():
            return Response(
                {"error": "Яндекс OAuth не настроен на сервере"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        state = secrets.token_urlsafe(32)
        cache.set(f"yandex_state:{state}", "1", timeout=STATE_TTL_SECONDS)

        params = {
            "response_type": "code",
            "client_id": settings.YANDEX_CLIENT_ID,
            "scope": "login:email login:info",
            "state": state,
        }
        redirect_uri = getattr(settings, "YANDEX_REDIRECT_URI", "")
        if redirect_uri:
            params["redirect_uri"] = redirect_uri

        url = f"{YANDEX_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
        return HttpResponseRedirect(url)


class YandexCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        if request.query_params.get("error"):
            return self._fail(request.query_params.get("error_description") or "Отказано в доступе")

        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            return self._fail("Не получен код авторизации")

        if not state or not cache.get(f"yandex_state:{state}"):
            return self._fail("Невалидный state — возможна CSRF-атака")
        cache.delete(f"yandex_state:{state}")

        if not _yandex_config_ok():
            return self._fail("Яндекс OAuth не настроен на сервере")

        try:
            token_data = self._exchange_code(code)
        except Exception as e:
            return self._fail(f"Ошибка обмена кода: {e}")

        access_token = token_data.get("access_token")
        if not access_token:
            return self._fail("Яндекс не вернул access_token")

        try:
            profile = self._fetch_profile(access_token)
        except Exception as e:
            return self._fail(f"Ошибка получения профиля: {e}")

        email = (profile.get("default_email") or "").strip().lower()
        if not email:
            return self._fail("В аккаунте Яндекса нет email")

        full_name = profile.get("real_name") or profile.get("display_name") or email

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User(
                email=email,
                full_name=full_name,
                role="Employee",
                position="",
                department="",
                public_id=uuid.uuid4(),
            )
            user.set_unusable_password()
            user.save()

        tokens = issue_tokens_for_user(user)
        ticket = secrets.token_urlsafe(32)
        cache.set(
            f"yandex_ticket:{ticket}",
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserPublicSerializer(user).data,
            },
            timeout=TICKET_TTL_SECONDS,
        )

        frontend_url = getattr(
            settings, "YANDEX_SUCCESS_REDIRECT", "/auth/yandex/success"
        )
        return HttpResponseRedirect(f"{frontend_url}?ticket={ticket}")

    @staticmethod
    def _exchange_code(code: str) -> dict:
        body = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.YANDEX_CLIENT_ID,
                "client_secret": settings.YANDEX_CLIENT_SECRET,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            YANDEX_TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _fetch_profile(access_token: str) -> dict:
        req = urllib.request.Request(
            f"{YANDEX_USERINFO_URL}?format=json",
            headers={"Authorization": f"OAuth {access_token}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _fail(message: str) -> HttpResponseRedirect:
        # При ошибке возвращаем юзера на страницу логина
        msg = urllib.parse.quote(message)
        return HttpResponseRedirect(f"/?yandex_error={msg}")


class YandexClaimView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        ticket = (request.data.get("ticket") or "").strip() if isinstance(request.data, dict) else ""
        if not ticket:
            return Response(
                {"error": "Не указан ticket"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = cache.get(f"yandex_ticket:{ticket}")
        if not payload:
            return Response(
                {"error": "Ticket недействителен или истёк"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cache.delete(f"yandex_ticket:{ticket}")

        return Response(
            {
                "success": True,
                "user": payload["user"],
                "tokens": {
                    "access": payload["access"],
                    "refresh": payload["refresh"],
                },
            }
        )
