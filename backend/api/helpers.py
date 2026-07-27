"""Общие вспомогательные функции, которые нужны сразу нескольким views.

Схема теперь нормализована (category <-> subcategory <-> skill,
role/department как M2M), а старому фронтенду по-прежнему удобнее получать
плоские строки ("category", "role", "department"). Эти функции — мост
между новой схемой и старым плоским API-контрактом.
"""
from .models import (
    Category,
    CategorySubcategory,
    Department,
    DepartmentUser,
    Role,
    Skill,
    Subcategory,
    SubcategorySkill,
    UserRole,
)

LEVEL_LABELS = {1: "Junior", 2: "Middle", 3: "Senior"}
LEVEL_LABEL_TO_INT = {v.lower(): k for k, v in LEVEL_LABELS.items()}


def skill_category_name(skill: Skill | None) -> str:
    """Имя первой связанной категории навыка (для отображения одной строкой)."""
    if skill is None:
        return ""
    category = (
        Category.objects.filter(subcategories__skills=skill)
        .values_list("name", flat=True)
        .first()
    )
    return category or ""


def skill_category_map() -> dict[int, str]:
    """skill_id -> имя категории одним проходом, без N+1 на списках скиллов."""
    mapping: dict[int, str] = {}
    for category in Category.objects.prefetch_related("subcategories__skills"):
        for subcategory in category.subcategories.all():
            for skill in subcategory.skills.all():
                mapping.setdefault(skill.id, category.name)
    return mapping


def attach_skill_to_category(skill: Skill, category_name: str) -> None:
    """Привязывает скилл к категории.

    В новой схеме между category и skill есть промежуточный слой —
    subcategory. Раз при создании скилла фронтенд передаёт только имя
    категории (без выбора подкатегории), заводим подкатегорию с тем же
    именем и используем её как техническое связующее звено.
    """
    category_name = (category_name or "").strip()
    if not category_name:
        return
    category, _ = Category.objects.get_or_create(name=category_name)
    subcategory, _ = Subcategory.objects.get_or_create(name=category_name)
    CategorySubcategory.objects.get_or_create(category=category, subcategory=subcategory)
    SubcategorySkill.objects.get_or_create(subcategory=subcategory, skill=skill)


def assign_role(user, role_name: str) -> None:
    role_name = (role_name or "").strip()
    if not role_name:
        return
    role, _ = Role.objects.get_or_create(name=role_name)
    UserRole.objects.get_or_create(user=user, role=role)


def assign_department(user, department_name: str) -> None:
    department_name = (department_name or "").strip()
    if not department_name:
        return
    department, _ = Department.objects.get_or_create(name=department_name)
    DepartmentUser.objects.get_or_create(user=user, department=department)