"""/api/public-profiles/{user_id} — публичный профиль сотрудника."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..helpers import LEVEL_LABELS, skill_category_name
from ..models import User, UserProject, UserSkill
from ..serializers import ErrorResponseSerializer, PublicProfileResponseSerializer


class PublicProfileView(APIView):
    @extend_schema(
        operation_id="public_profiles_retrieve",
        responses={200: PublicProfileResponseSerializer, 404: ErrorResponseSerializer},
    )
    def get(self, request, user_id: int):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )

        skills = (
            UserSkill.objects.select_related("skill")
            .filter(user_id=user.id, skill__isnull=False)
            .order_by("skill__name")
        )

        projects = (
            UserProject.objects.select_related("project")
            .filter(user_id=user.id)
            .order_by("project__name")
        )

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "fullName": user.full_name,
                    "position": user.position,
                    "department": user.primary_department,
                    "role": user.primary_role,
                },
                "skills": [
                    {
                        "userSkillId": us.id,
                        "skillId": us.skill_id,
                        "name": us.skill.name,
                        "category": skill_category_name(us.skill),
                        "level": LEVEL_LABELS.get(us.level, us.level),
                        "createdAt": us.created_at,
                        "updatedAt": us.updated_at,
                    }
                    for us in skills
                ],
                "projects": [
                    {
                        "id": up.project.id,
                        "name": up.project.name,
                        "description": up.project.description,
                        "status": up.project.status,
                        "startDate": up.project.start_date,
                        "endDate": up.project.end_date,
                        "joinedAt": up.joined_at,
                    }
                    for up in projects
                ],
            }
        )
