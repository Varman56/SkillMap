"""/profile/<user_id>/ — HTML-страница профиля, БЕЗ DRF.

Отдельный путь, отдельный рендер, без визуальной составляющей — фронт
оформит позже. Выводит из БД только те данные, что нужны для профиля.

Функционал (всё через обычный POST + ORM, без DRF):
- Редактирование phone/city/about. Должность (position) НЕ редактируется
  самим юзером — её меняют HR/Manager отдельно (тут не реализовано).
- Загрузка фото и резюме как реальных файлов (request.FILES). В БД поля
  photo/resume — TEXT, туда пишется только путь/URL к сохранённому файлу.
- Навыки: добавление нового (выбор из списка + уровень), изменение
  уровня существующего, удаление.

Все POST-запросы этой страницы различаются полем action в форме:
  update_profile / add_skill / update_skill / delete_skill
"""
from random import randint

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from api.models import DepartmentUser, Skill, User, UserProject, UserSkill

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_RESUME_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}

PROFILE_LEVEL_LABELS = {1: "Новичок", 2: "Опытный", 3: "Продвинутый", 4: "Эксперт"}
PROFILE_LEVEL_LABELS_EN = {1: "novice", 2: "experienced", 3: "advanced", 4: "expert"}
VALID_LEVELS = {1, 2, 3, 4}


def _save_uploaded_file(uploaded_file, subdir: str) -> str:
    """Сохраняет файл на диск (MEDIA_ROOT/subdir/...) и возвращает URL для записи в БД (TEXT)."""
    path = default_storage.save(f"{subdir}/{uploaded_file.name}", uploaded_file)
    return default_storage.url(path)


def _skill_display_name(skill) -> str:
    """'{подкатегория} ({скилл})', либо просто имя скилла, если подкатегории нет."""
    subcategory = skill.subcategories.first()
    if subcategory:
        return f"{subcategory.name} ({skill.name})"
    return skill.name


def _parse_level(raw_value):
    """Возвращает int уровня (1-4) или None, если значение некорректно."""
    try:
        level = int(raw_value)
    except (TypeError, ValueError):
        return None
    return level if level in VALID_LEVELS else None


def _handle_update_profile(request, user):
    user.phone = (request.POST.get("phone") or "").strip()
    user.city = (request.POST.get("city") or "").strip()
    user.about = (request.POST.get("about") or "").strip()

    photo = request.FILES.get("photo")
    if photo:
        if photo.content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
            messages.error(request, "Фото: разрешены только JPEG, PNG или WEBP")
        elif photo.size > MAX_PHOTO_SIZE:
            messages.error(request, "Фото: размер не должен превышать 5MB")
        else:
            user.photo = _save_uploaded_file(photo, "photos")

    resume = request.FILES.get("resume")
    if resume:
        if resume.content_type not in ALLOWED_RESUME_CONTENT_TYPES:
            messages.error(request, "Резюме: разрешены только PDF или DOCX")
        else:
            user.resume = _save_uploaded_file(resume, "resumes")

    user.save(update_fields=["phone", "city", "about", "photo", "resume"])
    messages.success(request, "Профиль обновлён")


def _handle_add_skill(request, user):
    skill_id = request.POST.get("skill_id")
    level = _parse_level(request.POST.get("level"))
    skill = Skill.objects.filter(id=skill_id, is_active=True).first()

    if not skill:
        messages.error(request, "Выбранный навык не найден")
        return
    if level is None:
        messages.error(request, "Уровень должен быть от 1 до 4")
        return

    _, created = UserSkill.objects.get_or_create(
        user=user,
        skill=skill,
        defaults={"level": level, "created_at": timezone.now()},
    )
    if created:
        messages.success(request, f"Навык «{skill.name}» добавлен")
    else:
        messages.error(request, f"Навык «{skill.name}» уже есть у пользователя")


def _handle_update_skill(request, user):
    user_skill = UserSkill.objects.filter(id=request.POST.get("user_skill_id"), user=user).first()
    level = _parse_level(request.POST.get("level"))

    if not user_skill:
        messages.error(request, "Навык не найден")
        return
    if level is None:
        messages.error(request, "Уровень должен быть 1, 2 или 3")
        return

    user_skill.level = level
    user_skill.updated_at = timezone.now()
    user_skill.is_approved = False
    user_skill.save(update_fields=["level", "updated_at"])
    messages.success(request, f"Уровень навыка «{user_skill.skill.name}» обновлён")


def _handle_delete_skill(request, user):
    deleted, _ = UserSkill.objects.filter(id=request.POST.get("user_skill_id"), user=user).delete()
    if deleted:
        messages.success(request, "Навык удалён")
    else:
        messages.error(request, "Навык не найден")


ACTION_HANDLERS = {
    "update_profile": _handle_update_profile,
    "add_skill": _handle_add_skill,
    "update_skill": _handle_update_skill,
    "delete_skill": _handle_delete_skill,
}


def _can_edit(request_user, profile_user) -> bool:
    """Редактировать профиль может сам пользователь, а также HR и Manager."""
    if request_user.id == profile_user.id:
        return True
    return request_user.has_role("HR", "Manager")


@login_required(login_url="/login/")
def profile_page(request, user_id=None):
    if user_id is None:
        user = request.user
    else:
        user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        if not _can_edit(request.user, user):
            return HttpResponseForbidden("Недостаточно прав для редактирования этого профиля")

        handler = ACTION_HANDLERS.get(request.POST.get("action"))
        if handler:
            handler(request, user)
        else:
            messages.error(request, "Неизвестное действие")

        if user_id is None:
            return redirect("my-profile")

        return redirect("profile-page", user_id=user.id)

    department_links = DepartmentUser.objects.select_related("department").filter(user_id=user.id)

    user_skills = (
        UserSkill.objects.select_related("skill")
        .prefetch_related("skill__subcategories")
        .filter(user_id=user.id, skill__isnull=False)
        .order_by("skill__name")
    )
    assigned_skill_ids = [us.skill_id for us in user_skills]
    available_skills_qs = (
        Skill.objects.filter(is_active=True)
        .exclude(id__in=assigned_skill_ids)
        .prefetch_related("subcategories")
        .order_by("name")
    )

    projects_qs = (
        UserProject.objects.select_related("project")
        .filter(user_id=user.id)
        .order_by("project__name")
    )
    search = (request.GET.get("search") or "").strip()
    if search:
        projects_qs = projects_qs.filter(project__name__icontains=search)

    departments = [link.department for link in department_links]
    context = {
        "profile_user": user,
        "can_edit": _can_edit(request.user, user),
        "departments_str": ", ".join(d.name for d in departments) or "—",
        "skills": [
            {
                "user_skill_id": us.id,
                "display_name": _skill_display_name(us.skill),
                "level": us.level,
                "level_label": PROFILE_LEVEL_LABELS.get(us.level, us.level),
                "level_class": PROFILE_LEVEL_LABELS_EN.get(us.level, us.level),
                "is_approved": us.is_approved,
            }
            for us in user_skills
        ],
        "available_skills": [
            {"id": skill.id, "display_name": _skill_display_name(skill)}
            for skill in available_skills_qs
        ],
        "levels": sorted(VALID_LEVELS),
        "projects": [
            {"name": up.project.name,
             "description": up.project.description,
             "icon": f"proj-icons/Project-icon-{randint(1, 5)}.svg",
             "id": up.project.id}
            for up in projects_qs
        ],
        "search": search,
    }
    return render(request, "profile.html", context)
