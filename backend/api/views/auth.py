"""/api/auth/* — логин, логаут, текущий пользователь."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
 
from ..models import User
from ..serializers import (
    ErrorResponseSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    LogoutRequestSerializer,
    SuccessResponseSerializer,
    UserPublicSerializer,
    issue_tokens_for_user,
)
 
 
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
 
    @extend_schema(
        operation_id="auth_login",
        request=LoginRequestSerializer,
        responses={
            200: LoginResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Некорректные данные для входа"},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]
 
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "Неверная почта или пароль"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
 
        if not user.check_password(password):
            return Response(
                {"success": False, "message": "Неверная почта или пароль"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
 
        tokens = issue_tokens_for_user(user)
        return Response(
            {
                "success": True,
                "user": UserPublicSerializer(user).data,
                "tokens": tokens,
            }
        )
 
 
class LogoutView(APIView):
    """Logout с JWT — клиент удаляет токены сам.
    Здесь опционально blacklist'им refresh-токен, если он передан.
    """
    permission_classes = [IsAuthenticated]
 
    @extend_schema(
        operation_id="auth_logout",
        request=LogoutRequestSerializer,
        responses={200: SuccessResponseSerializer},
    )
    def post(self, request):
        refresh_raw = request.data.get("refresh") if isinstance(request.data, dict) else None
        if refresh_raw:
            try:
                RefreshToken(refresh_raw).blacklist()
            except (TokenError, AttributeError):
                pass
        return Response({"success": True})
 
 
class MeView(APIView):
    permission_classes = [IsAuthenticated]
 
    @extend_schema(
        operation_id="auth_me",
        responses={200: UserPublicSerializer},
    )
    def get(self, request):
        return Response(UserPublicSerializer(request.user).data)