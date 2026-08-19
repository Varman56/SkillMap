"""Общие вспомогательные функции, которые нужны сразу нескольким views.

Схема теперь нормализована (category <-> subcategory <-> skill, role — M2M;
department у юзера — обычный FK, один отдел на юзера), а старому фронтенду
по-прежнему удобнее получать плоские строки ("category", "role",
"department"). Эти функции — мост между новой схемой и старым плоским
API-контрактом.
"""
from .models import (
    Category,
    CategorySubcategory,
    Department,
    Role,
    Skill,
    Subcategory,
    SubcategorySkill,
    UserRole,
)
from skillmap.views.profile_page import PROFILE_LEVEL_LABELS_EN

LEVEL_LABELS = PROFILE_LEVEL_LABELS_EN
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


def build_subcategories_cascade_data() -> list[dict]:
    """Список подкатегорий с привязанными к ним категориями (через "|" —
    удобно отдавать прямо в data-атрибут <option>) — нужно фронтенду для
    каскадного сужения "Подкатегория" при выборе "Категории" (см.
    reserve.html/matrix.html: без этого можно было выбрать категорию и
    подкатегорию из совсем разных веток дерева и получить нелогичный
    результат — см. историю бага в reserve_page.py)."""
    subcategories_qs = Subcategory.objects.prefetch_related("categories").order_by("name")
    return [
        {
            "name": sc.name,
            "categories": "|".join(sorted(c.name for c in sc.categories.all())),
        }
        for sc in subcategories_qs
    ]


def build_skills_cascade_data() -> list[dict]:
    """Список активных навыков с привязанными подкатегориями и
    (транзитивно, через них) категориями — тот же каскад, но для
    сужения "Навык" при выборе категории/подкатегории."""
    skills_qs = (
        Skill.objects.filter(is_active=True)
        .prefetch_related("subcategories__categories")
        .order_by("name")
    )
    skills_data = []
    for sk in skills_qs:
        subcategory_names = sorted(s.name for s in sk.subcategories.all())
        category_names = sorted({
            c.name for s in sk.subcategories.all() for c in s.categories.all()
        })
        skills_data.append({
            "name": sk.name,
            "subcategories": "|".join(subcategory_names),
            "categories": "|".join(category_names),
        })
    return skills_data


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
    """Назначает пользователю отдел (заменяет прежний, если был — отдел один)."""
    department_name = (department_name or "").strip()
    if not department_name:
        return
    department, _ = Department.objects.get_or_create(name=department_name)
    if user.department_id != department.id:
        user.department = department
        user.save(update_fields=["department"])