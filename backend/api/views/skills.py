"""/api/skills — справочник навыков и привязка к пользователям."""
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
 
from ..helpers import LEVEL_LABELS, attach_skill_to_category, skill_category_name
from ..models import Skill, UserSkill
from ..permissions import IsHR
from ..serializers import (
    AddUserSkillRequestSerializer,
    CreateSkillRequestSerializer,
    SkillSerializer,
    SkillShortSerializer,
    UpdateSkillLevelRequestSerializer,
)
 
 
class AvailableSkillsView(APIView):
    def get(self, request):
        skills = Skill.objects.filter(is_active=True).order_by("name")
        return Response(SkillShortSerializer(skills, many=True).data)
 
 
class AllSkillsView(APIView):
    def get(self, request):
        skills = Skill.objects.order_by("name")
        return Response(SkillSerializer(skills, many=True).data)
 
    def post(self, request):
        if not request.user.has_role("HR"):
            return Response(
                {"detail": "Только для HR"}, status=status.HTTP_403_FORBIDDEN
            )
 
        serializer = CreateSkillRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        name = serializer.validated_data["name"].strip()
        category = (serializer.validated_data.get("category") or "").strip()
 
        if Skill.objects.filter(name__iexact=name).exists():
            return Response(
                {"message": "Навык с таким названием уже существует"},
                status=status.HTTP_409_CONFLICT,
            )
 
        skill = Skill.objects.create(name=name, is_active=True)
        attach_skill_to_category(skill, category)
 
        return Response(
            SkillSerializer(skill).data,
            status=status.HTTP_201_CREATED,
        )
 
 
class MySkillsView(APIView):
    def post(self, request):
        serializer = AddUserSkillRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        skill_id = serializer.validated_data["skillId"]
        level = serializer.validated_data["level"]
 
        try:
            skill = Skill.objects.get(id=skill_id, is_active=True)
        except Skill.DoesNotExist:
            return Response(
                {"message": "Навык не найден"}, status=status.HTTP_404_NOT_FOUND
            )
 
        if UserSkill.objects.filter(user_id=request.user.id, skill_id=skill_id).exists():
            return Response(
                {"message": "Этот навык уже добавлен"},
                status=status.HTTP_409_CONFLICT,
            )
 
        try:
            user_skill = UserSkill.objects.create(
                user_id=request.user.id,
                skill_id=skill_id,
                level=level,
            )
        except IntegrityError:
            return Response(
                {"message": "Этот навык уже добавлен"},
                status=status.HTTP_409_CONFLICT,
            )
 
        return Response(
            {
                "Id": user_skill.id,
                "SkillId": user_skill.skill_id,
                "Name": skill.name,
                "Category": skill_category_name(skill),
                "Level": LEVEL_LABELS.get(user_skill.level, user_skill.level),
                "IsApproved": user_skill.is_approved,
                "CreatedAt": user_skill.created_at,
                "UpdatedAt": user_skill.updated_at,
            }
        )
 
 
class MySkillItemView(APIView):
    def delete(self, request, skill_id: int):
        deleted, _ = UserSkill.objects.filter(
            user_id=request.user.id, skill_id=skill_id
        ).delete()
        if deleted == 0:
            return Response(
                {"message": "Навык у пользователя не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True})
 
 
class MySkillLevelView(APIView):
    def patch(self, request, skill_id: int):
        serializer = UpdateSkillLevelRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        try:
            user_skill = UserSkill.objects.select_related("skill").get(
                user_id=request.user.id, skill_id=skill_id
            )
        except UserSkill.DoesNotExist:
            return Response(
                {"message": "Навык у пользователя не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        user_skill.level = serializer.validated_data["level"]
        user_skill.updated_at = timezone.now()
        user_skill.save(update_fields=["level", "updated_at"])
 
        return Response(
            {
                "Id": user_skill.id,
                "SkillId": user_skill.skill_id,
                "name": user_skill.skill.name if user_skill.skill else "",
                "category": skill_category_name(user_skill.skill),
                "Level": LEVEL_LABELS.get(user_skill.level, user_skill.level),
                "CreatedAt": user_skill.created_at,
                "UpdatedAt": user_skill.updated_at,
            }
        )
