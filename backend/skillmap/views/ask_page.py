"""/ask/ — HTML-страница «Кого спросить?», БЕЗ DRF.

GET ?skill=Docker — поиск сотрудников по навыку (или по названию
подкатегории/категории, куда навык входит).
Результаты группируются по максимальному уровню владения найденным
навыком (у одного user может совпасть несколько skills, берём лучший).
"""
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from api.models import UserSkill
from .profile_page import PROFILE_LEVEL_LABELS_EN, VALID_LEVELS

# Заголовки групп — множественное число, т.к. это шапка списка людей
# (в отличие от PROFILE_LEVEL_LABELS в profile_page.py, где бейдж на
# один-единственный навык одного человека, там нужно единственное число).
LEVEL_GROUP_LABELS = {4: "Эксперты", 3: "Продвинутые", 2: "Опытные", 1: "Новички"}


def _is_hr(user) -> bool:
    """Страница доступна только HR — остальных отправляем в их профиль."""
    return user.has_role("HR")


def _department_name(user) -> str:
    """Имя первого департамента пользователя.

    Специально не используем user.primary_department (models.py) — тот
    вызывает .departments.first(), а .first() всегда бьёт в БД заново
    и игнорирует prefetch_related, потому что у Department нет
    default-ordering и Django клонирует queryset через order_by('pk').
    Здесь department'ы уже prefetch'нуты, поэтому читаем через .all(),
    которая кэш использует (см. тот же приём в matrix.py).
    """
    departments = list(user.departments.all())
    return departments[0].name if departments else ""


def _search_users_by_skill(skill_q: str) -> list[dict]:
    if not skill_q:
        return []

    matches = (
        UserSkill.objects.select_related("user", "skill")
        .prefetch_related("user__departments")
        .filter(
            Q(skill__name__icontains=skill_q)
            | Q(skill__subcategories__name__icontains=skill_q)
            | Q(skill__subcategories__categories__name__icontains=skill_q),
            skill__is_active=True,
            user__is_active=True,
        )
        .distinct()
    )

    by_user: dict[int, list] = defaultdict(list)
    for us in matches:
        if us.user_id and us.skill_id:
            by_user[us.user_id].append(us)

    results = []
    for user_skills in by_user.values():
        best = max(user_skills, key=lambda us: us.level)
        user = best.user
        results.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "position": user.position,
                "department": _department_name(user),
                "photo": user.photo,
                "level": best.level,
                "matching_skills": sorted({us.skill.name for us in user_skills}),
            }
        )

    return results


def _group_by_level(flat_results: list[dict]) -> list[dict]:
    """Группирует плоский список найденных сотрудников по уровню навыка.

    Сортировка групп — от эксперта к новичку (лучших показываем первыми),
    поэтому VALID_LEVELS берём в обратном порядке.
    """
    by_level: dict[int, list] = defaultdict(list)
    for row in flat_results:
        by_level[row["level"]].append(row)

    groups = []
    for level in sorted(VALID_LEVELS, reverse=True):
        users = by_level.get(level, [])
        if not users:
            continue
        users.sort(key=lambda u: u["full_name"].lower())
        groups.append(
            {
                "level": level,
                "label": LEVEL_GROUP_LABELS.get(level, level),
                "level_class": PROFILE_LEVEL_LABELS_EN.get(level, level),
                "users": users,
            }
        )
    return groups


@login_required(login_url="/login/")
def ask_page(request):
    if not _is_hr(request.user):
        return redirect("my-profile")

    skill_q = (request.GET.get("skill") or "").strip()

    flat_results = _search_users_by_skill(skill_q)
    groups = _group_by_level(flat_results)

    context = {
        "search": skill_q,
        "has_search": bool(skill_q),
        "total_count": len(flat_results),
        "groups": groups,
    }
    return render(request, "ask.html", context)
