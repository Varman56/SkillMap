"""/api/users — управление пользователями (HR-only)."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
 
from ..helpers import assign_department, assign_role
from ..models import User
from ..permissions import IsHR
from ..serializers import CreateUserRequestSerializer, UserPublicSerializer
 
 
class UsersListCreateView(APIView):
    permission_classes = [IsHR]
 
    def get(self, request):
        users = User.objects.order_by("full_name")
        return Response(UserPublicSerializer(users, many=True).data)
 
    def post(self, request):
        serializer = CreateUserRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        data = serializer.validated_data
        email = data["email"].strip().lower()
 
        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"message": "Пользователь с таким email уже существует"},
                status=status.HTTP_409_CONFLICT,
            )
 
        user = User(
            email=email,
            full_name=data["fullName"].strip(),
            position=(data.get("position") or "").strip(),
            is_active=True,
        )
        user.set_password(data["password"])
        user.save()
 
        assign_role(user, data["role"].strip())
        assign_department(user, (data.get("department") or "").strip())
 
        return Response(UserPublicSerializer(user).data)
 
 
class UserDetailView(APIView):
    permission_classes = [IsHR]
 
    def get(self, request, user_id: int):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"message": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(UserPublicSerializer(user).data)
