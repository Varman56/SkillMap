"""/api/me/* — данные текущего пользователя."""
from rest_framework.response import Response
from rest_framework.views import APIView
 
from ..helpers import LEVEL_LABELS, skill_category_name
from ..models import User, UserProject, UserSkill
 
 
def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "fullName": user.full_name,
        "position": user.position,
        "department": user.primary_department,
        "role": user.primary_role,
    }
 
 
def _count_levels(qs) -> dict:
    levels = list(qs.values_list("level", flat=True))
    return {
        "totalSkills": len(levels),
        "seniorCount": sum(1 for l in levels if l == 3),
        "middleCount": sum(1 for l in levels if l == 2),
        "juniorCount": sum(1 for l in levels if l == 1),
    }
 
 
class MyDashboardView(APIView):
    def get(self, request):
        user: User = request.user
        search = (request.query_params.get("search") or "").strip().lower()
 
        skills_qs = UserSkill.objects.select_related("skill").filter(user_id=user.id)
        if search:
            skills_qs = skills_qs.filter(skill__name__icontains=search)
 
        user_skills = list(skills_qs.order_by("skill__name"))
 
        user_projects = (
            UserProject.objects.select_related("project")
            .filter(user_id=user.id)
            .order_by("project__name")
        )
 
        return Response(
            {
                "user": _serialize_user(user),
                "stats": _count_levels(skills_qs),
                "skills": [
                    {
                        "userSkillId": us.id,
                        "skillId": us.skill_id,
                        "name": us.skill.name if us.skill else "",
                        "category": skill_category_name(us.skill),
                        "level": LEVEL_LABELS.get(us.level, us.level),
                        "isApproved": us.is_approved,
                        "createdAt": us.created_at,
                        "updatedAt": us.updated_at,
                    }
                    for us in user_skills
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
                    for up in user_projects
                ],
            }
        )
 
 
class MySkillsListView(APIView):
    def get(self, request):
        user: User = request.user
        search = (request.query_params.get("search") or "").strip().lower()
 
        skills_qs = UserSkill.objects.select_related("skill").filter(user_id=user.id)
        if search:
            skills_qs = skills_qs.filter(skill__name__icontains=search)
 
        skills = skills_qs.order_by("skill__name")
 
        return Response(
            [
                {
                    "userSkillId": us.id,
                    "skillId": us.skill_id,
                    "name": us.skill.name if us.skill else "",
                    "category": skill_category_name(us.skill),
                    "level": LEVEL_LABELS.get(us.level, us.level),
                    "isApproved": us.is_approved,
                    "createdAt": us.created_at,
                    "updatedAt": us.updated_at,
                }
                for us in skills
            ]
        )
