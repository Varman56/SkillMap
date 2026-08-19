from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from api.helpers import build_skills_cascade_data, build_subcategories_cascade_data
from api.models import Category, Department, User

MAX_LEVEL = 4


def _is_hr_or_manager(user) -> bool:
    return user.is_authenticated and user.has_role("HR", "Manager")


def _build_category_columns():
    """Структура колонок: Категория -> Подкатегории -> Навыки."""
    columns = []
    categories = Category.objects.prefetch_related("subcategories__skills").order_by("name")
    for category in categories:
        subcategories_data = []
        for subcategory in category.subcategories.all():
            skills_data = []
            for skill in subcategory.skills.all():
                if skill.is_active:
                    skills_data.append({"id": skill.id, "name": skill.name})
            
            if skills_data:
                skills_data = sorted(skills_data, key=lambda x: x["name"])
                subcategories_data.append({
                    "name": subcategory.name,
                    "skills": skills_data,
                    "skill_count": len(skills_data) # Количество колонок для colspan подкатегории
                })
        
        if subcategories_data:
            subcategories_data = sorted(subcategories_data, key=lambda x: x["name"])
            total_category_skills = sum(sub["skill_count"] for sub in subcategories_data)
            columns.append({
                "name": category.name,
                "subcategories": subcategories_data,
                "skill_count": total_category_skills # Количество колонок для colspan категории
            })
    return columns


@login_required(login_url="/login/")
@user_passes_test(_is_hr_or_manager, login_url="/login/")
def matrix_page(request):
    user = request.user

    users_qs = User.objects.select_related("department").prefetch_related(
        "roles",
        "user_skills__skill",
    ).filter(is_active=True).order_by("full_name")
    # is_active=True — исключает уволенных (is_active=False у уволенных
    # значит "уволен", см. seed_demo_data.py/reserve_page.py). Раньше здесь
    # фильтра не было вообще, поэтому уволенный сотрудник продолжал
    # отображаться в матрице своего бывшего руководителя — несогласованно
    # с "Мой отдел" (department_page.py) и с резервом (только там уволенных
    # можно явно включить обратно галочкой "Только уволенные").

    if not user.has_role("HR") and user.has_role("Manager"):
        # Без назначенного отдела Manager'у буквально некого показывать
        # (тот же приём, что и в reserve_page.py/ask_page.py).
        users_qs = users_qs.filter(department_id=user.department_id) if user.department_id else users_qs.none()

    all_users = list(users_qs)

    columns = _build_category_columns()
    visible_skill_ids = {s["id"] for c in columns for sub in c["subcategories"] for s in sub["skills"]}

    employees = []
    for emp in all_users:
        # У одного навыка может быть до 2 строк одновременно (подтверждённая
        # + заявка на рассмотрении, см. docstring UserSkill). Сводим их в
        # одну ячейку для шаблона:
        #   level      — уровень контура иконки (больший из двух, "на что
        #                претендует" сотрудник);
        #   confirmed  — контур сплошной (весь навык подтверждён);
        #   fillLevel  — если задан и меньше level, то до этого уровня
        #                иконка залита сплошным (подтверждено), а
        #                оставшаяся часть до level — только контур
        #                (заявка на более высокий уровень ещё не
        #                подтверждена). См. includes/skill_icon.html.
        skills_by_id = {}
        raw_by_skill = {}
        for us in emp.user_skills.all():
            if us.skill_id in visible_skill_ids:
                raw_by_skill.setdefault(us.skill_id, {})[us.is_approved] = us.level

        for skill_id, by_status in raw_by_skill.items():
            approved_level = by_status.get(True)
            pending_level = by_status.get(False)

            if approved_level is not None and pending_level is not None:
                if approved_level >= pending_level:
                    # Заявка не выше уже подтверждённого — визуально она
                    # целиком "внутри" подтверждённого уровня, отдельно
                    # показывать нечего.
                    cell = {"level": approved_level, "confirmed": True, "fillLevel": None}
                else:
                    cell = {"level": pending_level, "confirmed": False, "fillLevel": approved_level}
            elif approved_level is not None:
                cell = {"level": approved_level, "confirmed": True, "fillLevel": None}
            else:
                cell = {"level": pending_level, "confirmed": False, "fillLevel": None}

            skills_by_id[skill_id] = cell

        employees.append(
            {
                "id": emp.id,
                "fullName": emp.full_name,
                "position": emp.position,
                "department": emp.primary_department,
                "role": emp.primary_role,
                "isIntern": emp.is_intern,
                "photo": emp.photo,
                "skills": skills_by_id,
            }
        )

    departments_list = list(Department.objects.values_list("name", flat=True).order_by("name"))
    categories_list = list(Category.objects.values_list("name", flat=True).order_by("name"))

    data = {
        "departments": departments_list,
        "categories": categories_list,
        # Подкатегории/навыки — списки словарей с data-categories/
        # data-subcategories (через "|") для каскадного сужения фильтров
        # в JS (см. build_subcategories_cascade_data/build_skills_cascade_
        # data в api/helpers.py — общие с reserve_page.py, чтобы дерево
        # "категория -> подкатегория -> навык" считалось одинаково в
        # обоих местах и не расходилось само с собой).
        "subcategories": build_subcategories_cascade_data(),
        "skills": build_skills_cascade_data(),
        "columns": columns,
        "employees": employees,
    }

    return render(request, "matrix.html", data)