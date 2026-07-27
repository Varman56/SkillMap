"""/api/matrix — матрица компетенций сотрудников (Manager/HR)."""
from rest_framework.response import Response
from rest_framework.views import APIView
 
from ..helpers import LEVEL_LABELS, skill_category_map
from ..models import Skill, User
from ..permissions import IsHROrManager
 
 
class MatrixView(APIView):
    permission_classes = [IsHROrManager]
 
    def get(self, request):
        users = list(
            User.objects.prefetch_related("user_skills__skill", "departments", "roles")
            .order_by("full_name")
        )
 
        skills = list(Skill.objects.filter(is_active=True).order_by("name"))
        category_by_skill = skill_category_map()
 
        departments = sorted({d.name for u in users for d in u.departments.all()})
 
        employees = []
        all_user_skills = []
        experts_count = 0
        interns_count = 0
 
        for u in users:
            if u.is_intern:
                interns_count += 1
 
            user_skills = [us for us in u.user_skills.all() if us.skill is not None]
            all_user_skills.extend(user_skills)
            if any(us.level == 3 for us in user_skills):
                experts_count += 1
 
            user_skills.sort(
                key=lambda us: (category_by_skill.get(us.skill_id, ""), us.skill.name or "")
            )
 
            employees.append(
                {
                    "id": u.id,
                    "fullName": u.full_name,
                    "position": u.position,
                    "department": u.primary_department,
                    "role": u.primary_role,
                    "isIntern": u.is_intern,
                    "skills": [
                        {
                            "skillId": us.skill_id,
                            "skillName": us.skill.name,
                            "skillCategory": category_by_skill.get(us.skill_id, ""),
                            "level": LEVEL_LABELS.get(us.level, us.level),
                            "createdAt": us.created_at,
                            "updatedAt": us.updated_at,
                        }
                        for us in user_skills
                    ],
                }
            )
 
        stats = {
            "totalEmployees": len(users),
            "uniqueSkills": len(skills),
            "experts": experts_count,
            "interns": interns_count,
            "seniorCount": sum(1 for us in all_user_skills if us.level == 3),
            "middleCount": sum(1 for us in all_user_skills if us.level == 2),
            "juniorCount": sum(1 for us in all_user_skills if us.level == 1),
        }
 
        return Response(
            {
                "stats": stats,
                "departments": departments,
                "skills": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "category": category_by_skill.get(s.id, ""),
                    }
                    for s in skills
                ],
                "employees": employees,
            }
        )
