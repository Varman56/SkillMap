"""/profile/<user_id>/ — HTML-страница профиля, БЕЗ DRF.

Отдельный путь, отдельный рендер, без визуальной составляющей — фронт
оформит позже. Выводит из БД только те данные, что нужны для профиля.

Функционал (всё через обычный POST + ORM, без DRF):
- Редактирование phone/city/about. Должность (position) НЕ редактируется
  самим юзером — её меняют HR/Manager отдельно (тут не реализовано).
- Загрузка фото как реального файла (request.FILES). В БД поле photo —
  TEXT, туда пишется только путь/URL к сохранённому файлу.
- Резюме — тоже реальный файл (TEXT-поле resume), но грузить и видеть
  его может ТОЛЬКО HR (см. can_manage_resume/_handle_update_resume/
  _handle_delete_resume) — обычный сотрудник (даже свой собственный
  профиль) и Manager резюме не видят и не грузят вовсе.
- Навыки: добавление нового (выбор из списка + уровень), изменение
  уровня существующей ЗАЯВКИ, удаление.

  У одного навыка может быть до двух строк UserSkill одновременно:
  подтверждённая (is_approved=True) и заявка на рассмотрении
  (is_approved=False) — см. docstring модели UserSkill в api/models.py.
  Добавление нового уровня НЕ трогает уже подтверждённый уровень: та
  строка живёт своей жизнью, пока HR/Manager не подтвердит новую заявку
  (см. approvals_page.py — там же старый подтверждённый уровень удаляется).
  Редактировать (менять уровень) можно только заявку, не подтверждённую
  строку — иначе пришлось бы либо тайно обходить подтверждение, либо
  заводить третью строку на один навык, а инвариант — максимум две.
- Комментарии (UserComment) — заметки HR/руководителя о сотруднике c
  оценкой 1-3 (см. COMMENT_LEVEL_LABELS). Виден и доступен для добавления
  список только HR (про любого сотрудника) и Manager (только про
  сотрудников своего отдела) — см. _can_manage_comments. Сам сотрудник
  комментарии о себе не видит НИКОГДА, даже если у него есть роль
  HR/Manager и он смотрит свой профиль. Редактировать/удалять может
  только автор конкретного комментария.

Все POST-запросы этой страницы различаются полем action в форме:
  update_profile / update_resume / delete_resume / add_skill /
  update_skill / delete_skill / add_comment / update_comment /
  delete_comment
"""
from random import randint

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from api.models import Skill, User, UserComment, UserProject, UserSkill

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_PHOTO_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_RESUME_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}

PROFILE_LEVEL_LABELS = {1: "Новичок", 2: "Опытный", 3: "Продвинутый", 4: "Эксперт"}
PROFILE_LEVEL_LABELS_EN = {1: "novice", 2: "experienced", 3: "advanced", 4: "expert"}
VALID_LEVELS = {1, 2, 3, 4}

# UserComment.level — оценка сотрудника автором комментария (1-3), см.
# docstring модуля выше и _can_manage_comments.
COMMENT_LEVEL_LABELS = {1: "Низкая", 2: "Средняя", 3: "Высокая"}
COMMENT_LEVEL_CLASS = {1: "low", 2: "medium", 3: "high"}


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

    user.save(update_fields=["phone", "city", "about", "photo"])
    messages.success(request, "Профиль обновлён")


def _handle_update_resume(request, user):
    """Загрузка/замена резюме — только HR (см. docstring модуля).

    Резюме больше не часть общей формы update_profile — раньше сотрудник
    мог загрузить резюме себе сам через тот же диалог, что и телефон/фото,
    теперь это отдельное действие, доступное только автору с ролью HR
    (независимо от того, свой это профиль или чужой).
    """
    if not request.user.has_role("HR"):
        messages.error(request, "Загружать резюме может только HR")
        return

    resume = request.FILES.get("resume")
    if not resume:
        messages.error(request, "Файл резюме не выбран")
        return
    if resume.content_type not in ALLOWED_RESUME_CONTENT_TYPES:
        messages.error(request, "Резюме: разрешены только PDF или DOCX")
        return

    user.resume = _save_uploaded_file(resume, "resumes")
    user.save(update_fields=["resume"])
    messages.success(request, "Резюме обновлено")


def _handle_delete_resume(request, user):
    if not request.user.has_role("HR"):
        messages.error(request, "Удалять резюме может только HR")
        return

    user.resume = None
    user.save(update_fields=["resume"])
    messages.success(request, "Резюме удалено")


def _approved_level(user, skill):
    """Уровень уже ПОДТВЕРЖДЁННОЙ строки (user, skill), либо None, если её нет.

    Используется, чтобы не дать создать/сохранить заявку (is_approved=False)
    на уровень не выше уже подтверждённого — такая заявка бессмысленна
    (просить подтвердить то, что не выше уже подтверждённого, незачем), и
    инвариант в этом проекте: строка «заявка» существует, только пока
    approved_level < pending_level (см. docstring UserSkill и комментарий
    в _handle_add_skill/_handle_update_skill ниже).
    """
    row = UserSkill.objects.filter(user=user, skill=skill, is_approved=True).only("level").first()
    return row.level if row else None


def _handle_add_skill(request, user):
    """Добавляет новую заявку на навык (is_approved=False).

    Разрешено, даже если у пользователя уже есть ПОДТВЕРЖДЁННЫЙ уровень
    этого навыка — так и запрашивается повышение (например, был Docker 2
    подтверждён, отдельной заявкой просим Docker 4), но ТОЛЬКО если новый
    уровень строго выше уже подтверждённого — иначе заявка не имеет
    смысла (см. _approved_level) и не создаётся вовсе. Также не разрешено,
    если по этому навыку уже есть заявка на рассмотрении — второй
    одновременно быть не может, инвариант «максимум 2 строки на навык»
    (см. UserSkill).
    """
    skill_id = request.POST.get("skill_id")
    level = _parse_level(request.POST.get("level"))
    skill = Skill.objects.filter(id=skill_id, is_active=True).first()

    if not skill:
        messages.error(request, "Выбранный навык не найден")
        return
    if level is None:
        messages.error(request, "Уровень должен быть от 1 до 4")
        return

    if UserSkill.objects.filter(user=user, skill=skill, is_approved=False).exists():
        messages.error(request, f"По навыку «{skill.name}» уже есть заявка на рассмотрении")
        return

    approved_level = _approved_level(user, skill)
    if approved_level is not None and level <= approved_level:
        messages.error(
            request,
            f"У вас уже подтверждён навык «{skill.name}» на уровне "
            f"{PROFILE_LEVEL_LABELS[approved_level]} — заявка имеет смысл только на более высокий уровень",
        )
        return

    UserSkill.objects.create(
        user=user, skill=skill, level=level, is_approved=False, created_at=timezone.now()
    )
    messages.success(request, f"Навык «{skill.name}» добавлен и отправлен на подтверждение")


def _handle_update_skill(request, user):
    """Меняет уровень в заявке (is_approved=False).

    Подтверждённую строку менять нельзя — у неё уже есть согласованный
    HR/Manager уровень; чтобы попросить другой, нужно завести новую заявку
    через add_skill (см. _handle_add_skill).

    Если у навыка уже есть подтверждённая строка, новый уровень заявки
    обязан быть строго выше неё — тот же инвариант, что и в add_skill (см.
    _approved_level). Опустить заявку до уровня подтверждённого или ниже
    нельзя — такая строка ничего не отражает, кроме уже согласованного
    факта, её просто нет смысла держать «на рассмотрении».
    """
    user_skill = UserSkill.objects.filter(
        id=request.POST.get("user_skill_id"), user=user, is_approved=False
    ).first()
    level = _parse_level(request.POST.get("level"))

    if not user_skill:
        messages.error(
            request,
            "Заявка не найдена, либо этот навык уже подтверждён — "
            "изменить подтверждённый уровень нельзя, добавьте новую заявку",
        )
        return
    if level is None:
        messages.error(request, "Уровень должен быть от 1 до 4")
        return

    approved_level = _approved_level(user, user_skill.skill)
    if approved_level is not None and level <= approved_level:
        messages.error(
            request,
            f"У вас уже подтверждён навык «{user_skill.skill.name}» на уровне "
            f"{PROFILE_LEVEL_LABELS[approved_level]} — заявка имеет смысл только на более высокий уровень",
        )
        return

    user_skill.level = level
    user_skill.updated_at = timezone.now()
    user_skill.save(update_fields=["level", "updated_at"])
    messages.success(request, f"Уровень навыка «{user_skill.skill.name}» обновлён")


def _handle_delete_skill(request, user):
    deleted, _ = UserSkill.objects.filter(id=request.POST.get("user_skill_id"), user=user).delete()
    if deleted:
        messages.success(request, "Навык удалён")
    else:
        messages.error(request, "Навык не найден")


def _parse_comment_level(raw_value):
    """Возвращает int оценки (1-3) или None, если значение некорректно."""
    try:
        level = int(raw_value)
    except (TypeError, ValueError):
        return None
    return level if level in COMMENT_LEVEL_LABELS else None


def _can_manage_comments(request_user, profile_user) -> bool:
    """Кто может писать/видеть комментарии о profile_user.

    HR — про любого сотрудника. Manager — только про сотрудников СВОЕГО
    отдела (тот же приём, что и в approvals_page.py/matrix_page.py). Про
    самого себя — никогда и никому, комментарий пишет HR/руководитель о
    сотруднике, не сотрудник сам о себе, и сам объект комментария эти
    заметки не видит вообще (даже если у него по совпадению тоже есть
    роль HR/Manager).
    """
    if request_user.id == profile_user.id:
        return False
    if request_user.has_role("HR"):
        return True
    if request_user.has_role("Manager"):
        return bool(profile_user.department_id) and profile_user.department_id == request_user.department_id
    return False


def _handle_add_comment(request, user):
    if not _can_manage_comments(request.user, user):
        messages.error(request, "Недостаточно прав для добавления комментария")
        return

    text = (request.POST.get("text") or "").strip()
    level = _parse_comment_level(request.POST.get("level"))

    if not text:
        messages.error(request, "Текст комментария не может быть пустым")
        return
    if level is None:
        messages.error(request, "Оценка должна быть от 1 до 3")
        return

    UserComment.objects.create(author=request.user, target_user=user, text=text, level=level)
    messages.success(request, "Комментарий добавлен")


def _handle_update_comment(request, user):
    """Менять комментарий может только его автор (см. _can_manage_comments —
    та проверка тоже нужна: например, если Manager сменил отдел, у него
    больше не должно быть доступа к старым комментариям того отдела)."""
    if not _can_manage_comments(request.user, user):
        messages.error(request, "Недостаточно прав")
        return

    comment = UserComment.objects.filter(
        id=request.POST.get("comment_id"), target_user=user, author=request.user
    ).first()
    text = (request.POST.get("text") or "").strip()
    level = _parse_comment_level(request.POST.get("level"))

    if not comment:
        messages.error(request, "Комментарий не найден, либо вы не его автор")
        return
    if not text:
        messages.error(request, "Текст комментария не может быть пустым")
        return
    if level is None:
        messages.error(request, "Оценка должна быть от 1 до 3")
        return

    comment.text = text
    comment.level = level
    comment.updated_at = timezone.now()
    comment.save(update_fields=["text", "level", "updated_at"])
    messages.success(request, "Комментарий обновлён")


def _handle_delete_comment(request, user):
    if not _can_manage_comments(request.user, user):
        messages.error(request, "Недостаточно прав")
        return

    deleted, _ = UserComment.objects.filter(
        id=request.POST.get("comment_id"), target_user=user, author=request.user
    ).delete()
    if deleted:
        messages.success(request, "Комментарий удалён")
    else:
        messages.error(request, "Комментарий не найден, либо вы не его автор")


ACTION_HANDLERS = {
    "update_profile": _handle_update_profile,
    "update_resume": _handle_update_resume,
    "delete_resume": _handle_delete_resume,
    "add_skill": _handle_add_skill,
    "update_skill": _handle_update_skill,
    "delete_skill": _handle_delete_skill,
    "add_comment": _handle_add_comment,
    "update_comment": _handle_update_comment,
    "delete_comment": _handle_delete_comment,
}


def _can_edit(request_user, profile_user) -> bool:
    """Редактировать профиль может сам пользователь, HR — любого, Manager —
    только сотрудников СВОЕГО отдела (тот же приём, что и в
    _can_manage_comments выше: раньше здесь для Manager не было проверки
    отдела вообще, и Manager мог отредактировать/удалить резюме и навыки
    сотрудника из чужого отдела, просто открыв его профиль по id)."""
    if request_user.id == profile_user.id:
        return True
    if request_user.has_role("HR"):
        return True
    if request_user.has_role("Manager"):
        return bool(profile_user.department_id) and profile_user.department_id == request_user.department_id
    return False


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

    user_skills = (
        UserSkill.objects.select_related("skill")
        .prefetch_related("skill__subcategories")
        .filter(user_id=user.id, skill__isnull=False)
        # Подтверждённая строка — первой в паре, чтобы в шаблоне
        # подтверждённый уровень навыка всегда шёл раньше заявки на новый.
        .order_by("skill__name", "-is_approved")
    )

    # Группируем строки по навыку — у одного навыка может быть до двух
    # строк (подтверждённая + заявка на рассмотрении), обе показываем
    # рядом под одним названием навыка (см. docstring UserSkill).
    grouped_skills = {}
    pending_skill_ids = set()
    for us in user_skills:
        if not us.is_approved:
            pending_skill_ids.add(us.skill_id)
        group = grouped_skills.setdefault(
            us.skill_id,
            {
                "skill_id": us.skill_id,
                "display_name": _skill_display_name(us.skill),
                "entries": [],
                # Временное поле, не уходит в шаблон — see ниже, удаляется
                # после цикла. Строки идут approved-первой (order_by выше),
                # так что к моменту обработки заявки этот уровень уже
                # известен.
                "_approved_level": None,
            },
        )
        if us.is_approved:
            group["_approved_level"] = us.level
        group["entries"].append(
            {
                "user_skill_id": us.id,
                "level": us.level,
                "level_label": PROFILE_LEVEL_LABELS.get(us.level, us.level),
                "level_class": PROFILE_LEVEL_LABELS_EN.get(us.level, us.level),
                "is_approved": us.is_approved,
            }
        )

    # Для заявки на рассмотрении в выпадающем списке уровня показываем
    # только уровни СТРОГО ВЫШЕ уже подтверждённого — те же правила, что
    # сервер и так проверит при сохранении (см. _approved_level в
    # _handle_update_skill), просто чтобы пользователь не мог даже выбрать
    # заведомо отклоняемое значение.
    for group in grouped_skills.values():
        approved_level = group.pop("_approved_level")
        allowed_levels = [
            level for level in sorted(VALID_LEVELS) if approved_level is None or level > approved_level
        ]
        for entry in group["entries"]:
            if not entry["is_approved"]:
                entry["allowed_levels"] = allowed_levels

    # Навык доступен для новой заявки, пока по нему нет заявки на
    # рассмотрении — даже если уже есть подтверждённый уровень (так и
    # запрашивается повышение, см. _handle_add_skill). approved_by_skill
    # нужен, чтобы в диалоге "Добавить навык" список уровней на лету
    # обрезался до допустимых (строго выше уже подтверждённого) —
    # см. data-approved-level в profile/_skill_dialog.html.
    approved_by_skill = {us.skill_id: us.level for us in user_skills if us.is_approved}
    available_skills_qs = (
        Skill.objects.filter(is_active=True)
        .exclude(id__in=pending_skill_ids)
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

    # Резюме — файл виден и загружается только HR (см. docstring модуля).
    can_manage_resume = request.user.has_role("HR")

    # Комментарии — HR про любого, Manager только про свой отдел, сам
    # объект комментария их не видит никогда (см. _can_manage_comments).
    can_manage_comments = _can_manage_comments(request.user, user)
    comments = []
    if can_manage_comments:
        comments = [
            {
                "id": c.id,
                "text": c.text,
                "level": c.level,
                "level_label": COMMENT_LEVEL_LABELS.get(c.level, c.level),
                "level_class": COMMENT_LEVEL_CLASS.get(c.level, ""),
                "author_name": c.author.full_name,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "is_mine": c.author_id == request.user.id,
            }
            for c in (
                UserComment.objects.select_related("author")
                .filter(target_user_id=user.id)
                .order_by("-created_at")
            )
        ]

    context = {
        "profile_user": user,
        "can_edit": _can_edit(request.user, user),
        "departments_str": user.department.name if user.department_id else "—",
        "skills": list(grouped_skills.values()),
        "available_skills": [
            {
                "id": skill.id,
                "display_name": _skill_display_name(skill),
                "approved_level": approved_by_skill.get(skill.id),
            }
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
        "can_manage_resume": can_manage_resume,
        "resume_url": user.resume if can_manage_resume else None,
        "can_manage_comments": can_manage_comments,
        "comments": comments,
        "comment_level_choices": sorted(COMMENT_LEVEL_LABELS.items()),
    }
    return render(request, "profile.html", context)
