from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from ..models import Category, Department, Skill, Subcategory, User

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

    users_qs = User.objects.prefetch_related(
        "departments",
        "roles",
        "user_skills__skill",
    ).order_by("full_name")

    if not user.has_role("HR") and user.has_role("Manager"):
        user_department_ids = user.departments.values_list("id", flat=True)
        users_qs = users_qs.filter(departments__id__in=user_department_ids).distinct()

    all_users = list(users_qs)

    columns = _build_category_columns()
    visible_skill_ids = {s["id"] for c in columns for sub in c["subcategories"] for s in sub["skills"]}

    employees = []
    for emp in all_users:
        skills_by_id = {}
        for us in emp.user_skills.all():
            if us.skill_id in visible_skill_ids:
                skills_by_id[us.skill_id] = {
                    "level": us.level,
                    "isApproved": us.is_approved,
                }

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
    subcategories_list = list(Subcategory.objects.values_list("name", flat=True).order_by("name"))
    skills_list = list(
        Skill.objects.filter(is_active=True).values_list("name", flat=True).order_by("name")
    )

    data = {
        "departments": departments_list,
        "categories": categories_list,
        "subcategories": subcategories_list,
        "skills": skills_list,
        "columns": columns,
        "employees": employees,
    }

    return render(request, "matrix.html", data)