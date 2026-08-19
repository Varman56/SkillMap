"""/ask/ — HTML-страница «Кого спросить?», БЕЗ DRF.

GET ?skill=Docker — поиск сотрудников по названию навыка (только по
самому навыку — раньше матчило ещё и по названию его подкатегории/
категории, но это путало: в карточке подписано "Совпавшие навыки", а там
оказывались навыки, которые сам текст запроса не содержал вообще —
просто потому что их категория содержала запрошенную подстроку).
Результаты группируются по максимальному уровню владения найденным
навыком (у одного user может совпасть несколько skills, берём лучший).

GET ?department=... — фильтр отдела. Доступен как выпадающий список
только HR (может выбрать любой отдел или оставить "Все отделы"); у
остальных ролей (Manager, Employee) поле залочено на их собственный
отдел — тот же приём (замок в UI + принудительная подстановка на
бэкенде), что и в reserve_page.py, см. _resolve_department.

Доступ: любой авторизованный.
"""
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from api.models import Department, UserSkill
from .profile_page import PROFILE_LEVEL_LABELS_EN, VALID_LEVELS

# Заголовки групп — множественное число, т.к. это шапка списка людей
# (в отличие от PROFILE_LEVEL_LABELS в profile_page.py, где бейдж на
# один-единственный навык одного человека, там нужно единственное число).
LEVEL_GROUP_LABELS = {4: "Эксперты", 3: "Продвинутые", 2: "Опытные", 1: "Новички"}

# Минимальная длина запроса — на 1 символе даже чистый поиск по названию
# навыка (без категории/подкатегории, см. _search_users_by_skill) даёт
# слишком широкий и малополезный результат (подстрока длиной 1 знак
# входит в кучу разных названий сразу). Та же логика, что в большинстве
# поисковых полей.
MIN_SEARCH_LENGTH = 2


def _resolve_department(request) -> tuple[str, bool]:
    """Возвращает (имя_отдела_для_фильтра, редактируем_ли_фильтр_на_странице).

    Только HR может выбрать любой отдел через ?department= (пустое
    значение — "Все отделы", без ограничения). Manager и Employee всегда
    видят только свой отдел — фильтр залочен (замок в UI) и здесь же
    принудительно подставляется их primary_department, даже если в query
    string прислано что-то другое: иначе ограничение легко обойти, просто
    исправив URL в адресной строке. Дословно тот же приём, что и в
    reserve_page.py._resolve_department.
    """
    if request.user.has_role("HR"):
        return (request.GET.get("department") or "").strip(), True
    return request.user.primary_department, False


def _department_name(user) -> str:
    """Имя отдела пользователя.

    Раньше здесь был обход .departments.first() с прицелом на кэш
    prefetch_related (M2M через DepartmentUser). Теперь отдел — обычный
    FK (User.department), поэтому это просто select_related-дружелюбное
    обращение к полю, без лишних запросов в БД.
    """
    return user.department.name if user.department_id else ""


def _search_users_by_skill(skill_q: str, department_scope) -> list[dict]:
    if not skill_q:
        return []
    if department_scope is not None and not department_scope:
        # Не-HR без назначенного отдела — искать буквально некого.
        return []

    matches = (
        UserSkill.objects.select_related("user", "user__department", "skill")
        .filter(
            skill__name__icontains=skill_q,
            skill__is_active=True,
            user__is_active=True,
        )
    )

    if department_scope is not None:
        matches = matches.filter(user__department__name=department_scope)

    matches = matches.distinct()

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
    department_filter, department_editable = _resolve_department(request)
    # department_scope для _search_users_by_skill: None — без ограничения
    # (HR с пустым фильтром = "Все отделы"), "" — искать некого (не-HR без
    # назначенного отдела), непустая строка — ограничить этим отделом.
    department_scope = department_filter or None if department_editable else department_filter

    skill_q = (request.GET.get("skill") or "").strip()
    search_too_short = bool(skill_q) and len(skill_q) < MIN_SEARCH_LENGTH

    flat_results = [] if search_too_short else _search_users_by_skill(skill_q, department_scope)
    groups = _group_by_level(flat_results)

    context = {
        "search": skill_q,
        "has_search": bool(skill_q) and not search_too_short,
        "search_too_short": search_too_short,
        "min_search_length": MIN_SEARCH_LENGTH,
        "total_count": len(flat_results),
        "groups": groups,
        "department_filter": department_filter,
        "department_editable": department_editable,
        "departments": Department.objects.order_by("name"),
    }
    return render(request, "ask.html", context)
