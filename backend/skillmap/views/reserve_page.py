"""/reserve/ — HTML-страница «Кадровый резерв», БЕЗ DRF.

Список сотрудников с широким набором фильтров: отдел, категория/подкатегория/
навык, диапазон уровня владения, статус подтверждения навыка, «только
практиканты», «только уволенные», поиск по ФИО/должности в одном поле.

Страница целиком управляется через GET, без единого POST — все фильтры
через query-параметры:
  ?department=...                 — точное имя отдела. Для HR — свободно;
                                     для Manager/Employee всегда принудительно
                                     их собственный отдел (см. _resolve_department)
  ?category=...                    — точное имя категории навыков
  ?subcategory=...                 — точное имя подкатегории
  ?skill=...                       — точное имя навыка
  ?status=approved|not_approved    — статус подтверждения навыка (UserSkill.is_approved)
  ?level_min=1&level_max=4         — диапазон уровня, границы см. VALID_LEVELS в profile_page.py
  ?only_interns=1                  — только практиканты (User.is_intern)
  ?only_terminated=1               — только уволенные (User.is_active=False);
                                     без этого флага показываются только активные
  ?search=...                      — по ФИО ИЛИ должности, одно поле на оба
  ?sort=recent                     — сортировка по дате добавления, свежие сверху
                                     (по умолчанию — по ФИО)

Доступ: любой авторизованный. Свобода выбора отдела — только у HR.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from api.models import Category, Department, Skill, Subcategory, User, UserSkill
from .profile_page import VALID_LEVELS

MIN_LEVEL = min(VALID_LEVELS)
MAX_LEVEL = max(VALID_LEVELS)


def _resolve_department(request) -> tuple[str, bool]:
    """Возвращает (имя_отдела_для_фильтра, редактируем_ли_фильтр_на_странице).

    HR может выбрать любой отдел через ?department=.
    Manager и Employee всегда видят только свой отдел — фильтр залочен
    (замок в UI) и здесь же принудительно подставляется их primary_department,
    даже если в query string прислано что-то другое: иначе ограничение
    легко обойти, просто исправив URL в адресной строке.
    """
    if request.user.has_role("HR"):
        return (request.GET.get("department") or "").strip(), True
    return request.user.primary_department, False


def _parse_level(raw, default: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(MIN_LEVEL, min(MAX_LEVEL, value))


@login_required(login_url="/login/")
def reserve_page(request):
    department_filter, department_editable = _resolve_department(request)
    category_filter = (request.GET.get("category") or "").strip()
    subcategory_filter = (request.GET.get("subcategory") or "").strip()
    skill_filter = (request.GET.get("skill") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    level_min = _parse_level(request.GET.get("level_min"), MIN_LEVEL)
    level_max = _parse_level(request.GET.get("level_max"), MAX_LEVEL)
    if level_min > level_max:
        # Не даём выставить "от 4 до 2" — вместо пустого результата
        # молча меняем местами, интервал всегда корректен.
        level_min, level_max = level_max, level_min
    only_interns = request.GET.get("only_interns") == "1"
    only_terminated = request.GET.get("only_terminated") == "1"
    search = (request.GET.get("search") or "").strip()
    sort = request.GET.get("sort") or ""

    users_qs = User.objects.prefetch_related("departments", "roles")
    users_qs = users_qs.filter(is_active=False) if only_terminated else users_qs.filter(is_active=True)

    if only_interns:
        users_qs = users_qs.filter(is_intern=True)

    if department_filter:
        users_qs = users_qs.filter(departments__name=department_filter)
    elif not department_editable:
        # Manager/Employee без назначенного отдела — им попросту нечего показывать.
        users_qs = users_qs.none()

    if search:
        users_qs = users_qs.filter(Q(full_name__icontains=search) | Q(position__icontains=search))

    skill_context = skill_filter or subcategory_filter or category_filter
    if skill_context:
        skill_matches = UserSkill.objects.filter(level__gte=level_min, level__lte=level_max)
        if status_filter == "approved":
            skill_matches = skill_matches.filter(is_approved=True)
        elif status_filter == "not_approved":
            skill_matches = skill_matches.filter(is_approved=False)

        if skill_filter:
            skill_matches = skill_matches.filter(skill__name=skill_filter)
        elif subcategory_filter:
            skill_matches = skill_matches.filter(skill__subcategories__name=subcategory_filter)
        elif category_filter:
            skill_matches = skill_matches.filter(skill__subcategories__categories__name=category_filter)

        users_qs = users_qs.filter(id__in=skill_matches.values_list("user_id", flat=True))

    users_qs = users_qs.distinct()
    users_qs = users_qs.order_by("-created_at") if sort == "recent" else users_qs.order_by("full_name")

    employees = [
        {
            "id": user.id,
            "full_name": user.full_name,
            "position": user.position,
            "photo": user.photo,
            "is_intern": user.is_intern,
            "is_active": user.is_active,
        }
        for user in users_qs
    ]

    context = {
        "employees": employees,
        "total_count": len(employees),
        "department_filter": department_filter,
        "department_editable": department_editable,
        "category_filter": category_filter,
        "subcategory_filter": subcategory_filter,
        "skill_filter": skill_filter,
        "status_filter": status_filter,
        "level_min": level_min,
        "level_max": level_max,
        "min_level": MIN_LEVEL,
        "max_level": MAX_LEVEL,
        "only_interns": only_interns,
        "only_terminated": only_terminated,
        "search": search,
        "sort": sort,
        "departments": Department.objects.order_by("name"),
        "categories": Category.objects.order_by("name"),
        "subcategories": Subcategory.objects.order_by("name"),
        "skills": Skill.objects.filter(is_active=True).order_by("name"),
    }
    return render(request, "reserve.html", context)
