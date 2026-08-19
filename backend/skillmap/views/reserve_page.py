"""/reserve/ — HTML-страница «Кадровый резерв», БЕЗ DRF.

Раньше страница была полностью server-side: каждый фильтр слался на
сервер новым GET-запросом (department/category/subcategory/skill/status/
level_min/level_max/only_interns/only_terminated/search/sort), из-за
чего при каждом клике перезагружалась вся страница — сначала это
пробовали лечить через AJAX-подгрузку (fetch того же URL без полной
навигации), но по итогу решили сделать так же, как в matrix_page.py/
matrix.html: сервер ОДИН РАЗ отдаёт вообще ВСЕХ сотрудников со всеми
данными, нужными для фильтрации, а дальше вся фильтрация — целиком на
JS (см. extra_js в reserve.html), без единого запроса к серверу вообще.

Из-за этого решения вся логика совмещения фильтров (категория/
подкатегория/навык через реальные M2M-связи Category->Subcategory->
Skill, диапазон уровня, статус подтверждения и т.д. — та самая, что
чинили из-за бага с несовместимыми фильтрами) теперь ПРОДУБЛИРОВАНА на
JS. Это осознанный компромисс: два места с одной и той же бизнес-
логикой придётся держать в синхроне вручную, если что-то в правилах
фильтрации изменится.

Списки подкатегорий/навыков с данными для каскада (data-categories/
data-subcategories) теперь строит api/helpers.py (build_subcategories_
cascade_data/build_skills_cascade_data) — та же самая функция, что
использует и matrix_page.py, чтобы в обоих местах карточка "категория ->
подкатегория -> навык" считалась ОДИНАКОВО, без дублирования в двух
view-файлах.

Доступ: только HR (см. _can_view) — остальных отправляем в их профиль,
тот же приём, что и в approvals_page.py.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from api.helpers import build_skills_cascade_data, build_subcategories_cascade_data
from api.models import Category, Department, User
from .profile_page import VALID_LEVELS

MIN_LEVEL = min(VALID_LEVELS)
MAX_LEVEL = max(VALID_LEVELS)


def _can_view(user) -> bool:
    return user.has_role("HR")


def _build_employees():
    users_qs = (
        User.objects.select_related("department")
        .prefetch_related("user_skills__skill__subcategories__categories")
        .order_by("full_name")
    )

    employees = []
    for user in users_qs:
        skills = []
        for user_skill in user.user_skills.all():
            skill = user_skill.skill
            subcategory_names = sorted(s.name for s in skill.subcategories.all())
            category_names = sorted({
                c.name for s in skill.subcategories.all() for c in s.categories.all()
            })
            skills.append({
                "skill": skill.name,
                "level": user_skill.level,
                "approved": user_skill.is_approved,
                "subcategories": subcategory_names,
                "categories": category_names,
            })

        employees.append({
            "id": user.id,
            "full_name": user.full_name,
            "position": user.position or "",
            "photo": user.photo,
            "is_intern": user.is_intern,
            "is_active": user.is_active,
            "department": user.department.name if user.department_id else "",
            # Целое число, не float — Django рендерит float с запятой как
            # разделитель дробной части (локаль), и JS Number("...,...")
            # в data-атрибуте молча даёт NaN, из-за чего сортировка
            # "Последние добавленные" переставала работать без единой
            # ошибки в консоли.
            "created_ts": int(user.created_at.timestamp()) if user.created_at else 0,
            "skills": skills,
            # id для {% json_script %} в шаблоне — там же, где карточка,
            # лежит <script type="application/json"> с этим списком навыков,
            # JS читает его по id при фильтрации/сравнении с фильтрами.
            "skills_json_id": f"skills-data-{user.id}",
        })
    return employees


@login_required(login_url="/login/")
def reserve_page(request):
    if not _can_view(request.user):
        return redirect("my-profile")

    context = {
        "employees": _build_employees(),
        "min_level": MIN_LEVEL,
        "max_level": MAX_LEVEL,
        # Все уровни между MIN_LEVEL и MAX_LEVEL — для подписей "1 2 3 4"
        # под слайдером диапазона уровня (раньше подписывались только
        # края диапазона, средние уровни были не подписаны).
        "levels": list(range(MIN_LEVEL, MAX_LEVEL + 1)),
        "departments": Department.objects.order_by("name"),
        "categories": Category.objects.order_by("name"),
        "subcategories": build_subcategories_cascade_data(),
        "skills": build_skills_cascade_data(),
    }
    return render(request, "reserve.html", context)
