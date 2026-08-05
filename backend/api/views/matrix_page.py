"""/matrix-data/ — данные для SPA-страницы "Матрица компетенций отдела".

Не HTML, не DRF-ручка — просто Python-функция, которая собирает всё
нужное для этой страницы прямо из БД и отдаёт JSON (через JsonResponse).
Фронт сам рисует таблицу/пироги/графики — эта функция только словарь
с данными, ничего больше (по аналогии с profile_page.py, только вместо
HTML-шаблона на выходе JSON для SPA-фетча).

Доступ: только HR/Manager (та же логика, что и в DRF MatrixView).

Фильтрация — через query-параметры:
  ?search=...        — по ФИО, должности, отделу
  ?department=...     — точное имя отдела
  ?category=...        — точное имя категории навыков
  ?subcategory=...      — точное имя подкатегории
  ?level_min=1&level_max=4  — диапазон уровня навыка
  ?status=approved|not_approved  — статус подтверждения навыка
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse

from ..models import Category, Skill, User, UserSkill

MAX_LEVEL = 4


def _is_hr_or_manager(user) -> bool:
    return user.is_authenticated and user.has_role("HR", "Manager")


def _build_category_columns():
    """Структура колонок для шапки таблицы: категория -> список навыков."""
    columns = []
    categories = Category.objects.prefetch_related("subcategories__skills").order_by("name")
    for category in categories:
        skills_seen = {}
        for subcategory in category.subcategories.all():
            for skill in subcategory.skills.all():
                if skill.is_active:
                    skills_seen[skill.id] = skill.name
        if skills_seen:
            columns.append(
                {
                    "category": category.name,
                    "skills": [
                        {"id": skill_id, "name": name}
                        for skill_id, name in sorted(skills_seen.items(), key=lambda kv: kv[1])
                    ],
                }
            )
    return columns


@login_required(login_url="/")
@user_passes_test(_is_hr_or_manager, login_url="/")
def matrix_page_data(request):
    search = (request.GET.get("search") or "").strip()
    department_filter = (request.GET.get("department") or "").strip()
    category_filter = (request.GET.get("category") or "").strip()
    subcategory_filter = (request.GET.get("subcategory") or "").strip()
    skill_filter = (request.GET.get("skill") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()  # approved / not_approved
    level_min = request.GET.get("level_min")
    level_max = request.GET.get("level_max")

    try:
        level_min = int(level_min) if level_min else 1
    except ValueError:
        level_min = 1
    try:
        level_max = int(level_max) if level_max else MAX_LEVEL
    except ValueError:
        level_max = MAX_LEVEL

    users_qs = (
        User.objects.prefetch_related(
            "departments",
            "roles",
            "user_skills__skill__subcategories__categories",
        )
        .order_by("full_name")
    )
    if search:
        users_qs = (
            users_qs.filter(full_name__icontains=search)
            | users_qs.filter(position__icontains=search)
            | users_qs.filter(departments__name__icontains=search)
            | users_qs.filter(user_skills__skill__name__icontains=search)
        )
        users_qs = users_qs.distinct()
    if department_filter:
        users_qs = users_qs.filter(departments__name=department_filter).distinct()

    all_users = list(users_qs)

    columns = _build_category_columns()
    if category_filter:
        columns = [c for c in columns if c["category"] == category_filter]
    if subcategory_filter:
        # подкатегория не хранится прямо в структуре колонок (там только категория+скилл),
        # поэтому фильтруем колонки по навыкам, реально относящимся к этой подкатегории
        allowed_skill_ids = set(
            UserSkill.objects.filter(skill__subcategories__name=subcategory_filter).values_list(
                "skill_id", flat=True
            )
        )
        for column in columns:
            column["skills"] = [s for s in column["skills"] if s["id"] in allowed_skill_ids]
        columns = [c for c in columns if c["skills"]]

    visible_skill_ids = {s["id"] for c in columns for s in c["skills"]}
    if skill_filter:
        visible_skill_ids = {
            sid for sid in visible_skill_ids
            if Skill.objects.filter(id=sid, name=skill_filter).exists()
        }
        for column in columns:
            column["skills"] = [s for s in column["skills"] if s["id"] in visible_skill_ids]
        columns = [c for c in columns if c["skills"]]

    employees = []
    all_relevant_user_skills = []
    high_level_user_ids = set()

    for user in all_users:
        skills_by_id = {}
        for us in user.user_skills.all():
            if us.skill is None or us.skill_id not in visible_skill_ids:
                continue
            if not (level_min <= us.level <= level_max):
                continue
            if status_filter == "approved" and not us.is_approved:
                continue
            if status_filter == "not_approved" and us.is_approved:
                continue
            skills_by_id[us.skill_id] = {"level": us.level, "isApproved": us.is_approved}
            all_relevant_user_skills.append(us)
            if us.level == MAX_LEVEL:
                high_level_user_ids.add(user.id)

        employees.append(
            {
                "id": user.id,
                "fullName": user.full_name,
                "position": user.position,
                "department": user.primary_department,
                "role": user.primary_role,
                "isIntern": user.is_intern,
                "photo": user.photo,
                "skills": skills_by_id,  # {skill_id: {level, isApproved}}, пропущенных навыков нет в словаре
            }
        )

    total_skill_entries = len(all_relevant_user_skills)
    approved_count = sum(1 for us in all_relevant_user_skills if us.is_approved)

    average_level_percent = (
        round(sum(us.level for us in all_relevant_user_skills) / total_skill_entries / MAX_LEVEL * 100, 1)
        if total_skill_entries
        else 0
    )
    approved_percent = round(approved_count / total_skill_entries * 100, 1) if total_skill_entries else 0
    not_approved_percent = round(100 - approved_percent, 1) if total_skill_entries else 0

    # Навыки, требующие развития — средний уровень по навыку ниже 3
    skill_levels: dict[int, list[int]] = {}
    skill_names: dict[int, str] = {}
    for us in all_relevant_user_skills:
        skill_levels.setdefault(us.skill_id, []).append(us.level)
        skill_names[us.skill_id] = us.skill.name
    skills_needing_development = [
        skill_names[skill_id]
        for skill_id, levels in skill_levels.items()
        if sum(levels) / len(levels) < 3
    ]

    data = {
        "stats": {
            "totalEmployees": len(all_users),
            "averageLevelPercent": average_level_percent,
            "approvedPercent": approved_percent,
            "notApprovedPercent": not_approved_percent,
            "highLevelEmployees": {
                "count": len(high_level_user_ids),
                "total": len(all_users),
                "percent": round(len(high_level_user_ids) / len(all_users) * 100, 1) if all_users else 0,
            },
            "skillsNeedingDevelopment": {
                "count": len(skills_needing_development),
                "skillNames": skills_needing_development,
            },
        },
        "filters": {
            "departments": list(
                User.objects.values_list("departments__name", flat=True).exclude(departments__name=None).distinct()
            ),
            "categories": [c["category"] for c in _build_category_columns()],
            "skills": sorted({s["name"] for c in _build_category_columns() for s in c["skills"]}),
        },
        "columns": columns,
        "employees": employees,
    }
    return JsonResponse(data)
