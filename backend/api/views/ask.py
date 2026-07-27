"""/api/ask — поиск сотрудников по навыку."""
from collections import defaultdict
 
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
 
from ..models import UserSkill
 
LEVEL_TO_UI = {1: "experienced", 2: "advanced", 3: "expert"}
 
 
class AskView(APIView):
    def get(self, request):
        skill_q = (request.query_params.get("skill") or "").strip().lower()
        if not skill_q:
            return Response([])
 
        matches = list(
            UserSkill.objects.select_related("user", "skill")
            .filter(
                Q(skill__name__icontains=skill_q)
                | Q(skill__subcategories__name__icontains=skill_q)
                | Q(skill__subcategories__categories__name__icontains=skill_q)
            )
            .distinct()
        )
 
        by_user = defaultdict(list)
        for us in matches:
            if us.user is None or us.skill is None:
                continue
            by_user[us.user_id].append(us)
 
        results = []
        for user_skills in by_user.values():
            best = max(user_skills, key=lambda us: us.level)
            user = best.user
            matching = sorted({us.skill.name for us in user_skills})
            results.append(
                {
                    "id": user.id,
                    "fullName": user.full_name,
                    "position": user.position,
                    "department": user.primary_department,
                    "_level": best.level,
                    "matchingSkills": matching,
                }
            )
 
        results.sort(key=lambda r: r["_level"], reverse=True)
        for r in results:
            r["level"] = LEVEL_TO_UI.get(r.pop("_level"), "experienced")
        return Response(results)