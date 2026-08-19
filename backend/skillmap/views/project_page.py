"""/projects/<project_id>/ — HTML-страница проекта, БЕЗ DRF.

Отдельный путь, отдельный рендер — по той же схеме, что и profile_page.py.
Смотреть проект может любой авторизованный, редактировать (и название, и
статус, и даты, и состав участников) — ТОЛЬКО владелец проекта
(`Project.created_by`), назначенный при создании проекта. Раньше это право
было у любого HR/Manager вообще, независимо от того, чей это проект —
сужено по явному запросу до конкретного руководителя (см. `_can_edit`).
Демоданные (`seed_demo_data.py`) теперь всегда назначают created_by
кому-то из Manager при создании проекта.

Все POST-запросы этой страницы различаются полем action в форме:
  update_project / add_member / remove_member

GET ?search=... — фильтр списка участников по ФИО (подстрока, без учёта регистра).
"""
from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from api.models import Project, User, UserProject

# Статус хранится в БД как обычная строка (Project.status — CharField, не
# choices на уровне модели), но в UI должен быть закрытым списком с
# понятными подписями и цветом-индикатором — тот же приём, что и с
# уровнями навыков (PROFILE_LEVEL_LABELS в profile_page.py). Ключ — то,
# что реально лежит в БД (совпадает с тем, что пишет seed_demo_data.py).
STATUS_META = {
    "Active": {"label": "В работе", "css_class": "active"},
    "On Hold": {"label": "Приостановлен", "css_class": "on-hold"},
    "Completed": {"label": "Завершён", "css_class": "completed"},
}
DEFAULT_STATUS = "Active"


def _can_edit(user, project) -> bool:
    """Редактировать проект (и управлять участниками) может только его
    владелец — project.created_by. Раньше это было у любого HR/Manager;
    теперь право явно сужено до конкретного руководителя, назначенного
    этому проекту (см. docstring модуля)."""
    return user.is_authenticated and project.created_by_id == user.id


def _parse_date_field(request, field_name):
    """Разбирает <input type="date"> (YYYY-MM-DD) в aware datetime на
    начало дня, либо None, если поле пустое. Возвращает (value, ok) —
    ok=False, если поле непустое, но не парсится как дата."""
    raw = (request.POST.get(field_name) or "").strip()
    if not raw:
        return None, True

    parsed = parse_date(raw)
    if parsed is None:
        return None, False

    return timezone.make_aware(datetime.combine(parsed, time.min)), True


def _handle_update_project(request, project):
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "Название проекта обязательно")
        return

    status = (request.POST.get("status") or project.status or DEFAULT_STATUS).strip()
    if status not in STATUS_META:
        messages.error(request, "Неизвестный статус проекта")
        return

    start_date, start_ok = _parse_date_field(request, "start_date")
    end_date, end_ok = _parse_date_field(request, "end_date")
    if not start_ok:
        messages.error(request, "Некорректная дата начала проекта")
        return
    if not end_ok:
        messages.error(request, "Некорректная дата окончания проекта")
        return
    if start_date and end_date and end_date < start_date:
        messages.error(request, "Дата окончания раньше даты начала")
        return

    project.name = name
    project.status = status
    project.start_date = start_date
    project.end_date = end_date
    project.save(update_fields=["name", "status", "start_date", "end_date"])
    messages.success(request, "Проект обновлён")


def _handle_update_description(request, project):
    """Сведения теперь редактируются отдельной формой прямо на странице
    (inline, вместо маленького textarea в общей модалке) — поле может
    содержать очень длинный текст, и в тесной модалке это было неудобно.
    Своё action, чтобы не гонять туда-сюда остальные поля проекта."""
    project.description = (request.POST.get("description") or "").strip()
    project.save(update_fields=["description"])
    messages.success(request, "Сведения обновлены")


def _handle_add_member(request, project):
    user = User.objects.filter(id=request.POST.get("user_id")).first()

    if not user:
        messages.error(request, "Пользователь не найден")
        return

    _, created = UserProject.objects.get_or_create(
        user=user,
        project=project,
        defaults={"joined_at": timezone.now()},
    )
    if created:
        messages.success(request, f"«{user.full_name}» добавлен в проект")
    else:
        messages.error(request, f"«{user.full_name}» уже состоит в проекте")


def _handle_remove_member(request, project):
    user_id = request.POST.get("user_id")
    # Владелец проекта обязан оставаться в числе его участников (см.
    # docstring модуля и seed_demo_data.py) — иначе получится нелогичная
    # ситуация "владелец есть, а среди участников — нет".
    if str(project.created_by_id) == str(user_id):
        messages.error(request, "Нельзя удалить владельца проекта из участников")
        return

    deleted, _ = UserProject.objects.filter(project=project, user_id=user_id).delete()
    if deleted:
        messages.success(request, "Участник удалён из проекта")
    else:
        messages.error(request, "Участник не найден в проекте")


ACTION_HANDLERS = {
    "update_project": _handle_update_project,
    "update_description": _handle_update_description,
    "add_member": _handle_add_member,
    "remove_member": _handle_remove_member,
}


@login_required(login_url="/login/")
def project_page(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("created_by"), id=project_id
    )
    can_edit = _can_edit(request.user, project)

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Недостаточно прав для редактирования этого проекта")

        handler = ACTION_HANDLERS.get(request.POST.get("action"))
        if handler:
            handler(request, project)
        else:
            messages.error(request, "Неизвестное действие")

        return redirect("project-page", project_id=project.id)

    member_links = (
        UserProject.objects.select_related("user")
        .filter(project_id=project.id, user__is_active=True)
        .order_by("user__full_name")
    )
    # user__is_active=True — уволенные сотрудники (is_active=False, см.
    # seed_demo_data.py/reserve_page.py) не показываются в списке
    # участников, тем же принципом, что уже применён в matrix_page.py/
    # approvals_page.py/department_page.py. Раньше фильтра не было —
    # найдено и исправлено по итогам того же ревью, что и там (см. аудит).
    # Карточка "Владелец" (project.created_by, ниже по контексту) этим
    # фильтром не затронута и продолжит показывать владельца, даже если
    # он вдруг окажется уволен, — редкий крайний случай, отдельно не
    # обрабатывается.
    member_count = member_links.count()

    search = (request.GET.get("search") or "").strip()
    if search:
        member_links = member_links.filter(user__full_name__icontains=search)

    available_users_qs = (
        User.objects.filter(is_active=True)
        .exclude(id__in=UserProject.objects.filter(project_id=project.id).values_list("user_id", flat=True))
        .order_by("full_name")
    )

    status_meta = STATUS_META.get(project.status, {"label": project.status or "—", "css_class": "unknown"})

    context = {
        "project": project,
        "owner": project.created_by,
        "can_edit": can_edit,
        "status_label": status_meta["label"],
        "status_css_class": status_meta["css_class"],
        "status_choices": [
            {"value": value, "label": meta["label"]}
            for value, meta in STATUS_META.items()
        ],
        "members": [
            {
                "id": link.user.id,
                "full_name": link.user.full_name,
                "position": link.user.position,
                "photo": link.user.photo,
                "joined_at": link.joined_at,
                # Владелец — тоже участник (см. seed_demo_data.py и
                # _handle_remove_member), но убрать его из списка через
                # корзину нельзя — помечаем, чтобы шаблон не рисовал
                # кнопку удаления на его строке.
                "is_owner": link.user.id == project.created_by_id,
            }
            for link in member_links
        ],
        "member_count": member_count,
        "available_users": available_users_qs,
        "search": search,
    }
    return render(request, "project.html", context)
