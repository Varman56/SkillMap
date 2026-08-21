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

Поиск по списку участников — целиком на клиенте (см. extra_js в
project.html, data-search на каждой .proj-member-row), без похода на
сервер: сервер всегда рендерит ПОЛНЫЙ список участников, JS только
показывает/прячет строки по подстроке. Раньше это был GET ?search=...
с перезагрузкой страницы на каждое нажатие — по тому же принципу, что
уже applied в ask.html/reserve.html/projects.html, унифицировано.

Диалог "Добавить участника" — по запросу у каждого кандидата в выпадающем
списке теперь видна должность (и есть клиентский фильтр по отделу рядом,
без похода на сервер) — раньше список показывал только ФИО, что было
неудобно, если руководитель хочет добавить конкретного специалиста из
ЧУЖОГО отдела (например "нужен кто-то из DevOps, но с определённой
должностью") и не помнит его по имени. См. available_users в контексте и
extra_js в project.html.
"""
from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from api.models import Department, Project, User, UserProject

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
    """Редактировать проект (и управлять участниками) может его
    владелец — project.created_by, — а также HR. Раньше это было у любого
    HR/Manager; затем право сузили до конкретного руководителя, назначенного
    этому проекту (см. docstring модуля). Но created_by — ForeignKey с
    on_delete=SET_NULL (см. api/models.py), и если он когда-нибудь станет
    NULL (сейчас в приложении нет функции удаления пользователя или
    переназначения владельца проекта, но модель это допускает), проект без
    HR-доступа стал бы НАВСЕГДА неуправляемым — ни для кого, включая HR
    (аудит, п. 2.4). HR — та же роль, что уже имеет отдельный override для
    похожей ситуации в profile_page.py._can_edit (HR может редактировать
    любой профиль), поэтому здесь применена та же конвенция."""
    if not user.is_authenticated:
        return False
    return project.created_by_id == user.id or user.has_role("HR")


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

    # Project.name — CharField(max_length=255), но без явной проверки
    # длины здесь имя длиннее 255 символов доходило бы необработанным до
    # .save() ниже — на Postgres это падает необработанным DataError
    # (500), а не аккуратным сообщением, как остальные поля этой формы
    # (аудит, п. 4.8). max_length берётся с самого поля модели, а не
    # хардкодится числом — если он когда-нибудь изменится в models.py,
    # проверка здесь не разъедется с ним сама по себе.
    max_name_length = Project._meta.get_field("name").max_length
    if len(name) > max_name_length:
        messages.error(request, f"Название проекта не должно превышать {max_name_length} символов")
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
    # User.id — IntegerField: filter(id=...) с пустой строкой или
    # нечисловым значением падает необработанным ValueError прямо при
    # построении SQL (а не при обращении к БД), то есть до всякой
    # проверки "пользователь не найден" ниже. Ровно так и приходило —
    # <select> в диалоге стартует с пустого <option value="">, защищённого
    # только required на HTML-уровне (не защита вообще, если POST ушёл в
    # обход JS/формы) — аудит, п. 2.5. Тот же приём, что уже применён в
    # _handle_remove_member для user_id (см. там же, аудит п. 2.3).
    try:
        user_id = int(request.POST.get("user_id"))
    except (TypeError, ValueError):
        messages.error(request, "Некорректный сотрудник")
        return

    # is_active=True, is_intern=False — <select> в диалоге собирается из
    # available_users_qs (см. project_page() ниже), который уже фильтрует
    # и то, и другое, но сам обработчик POST раньше принимал ЛЮБОЙ
    # существующий user_id без перепроверки — можно было добавить
    # уволенного сотрудника прямым POST в обход диалога (аудит, п. 4.9);
    # такая "мёртвая" строка потом нигде не управляется — не видна в
    # обычном списке участников (member_links ниже фильтрует
    # user__is_active=True), не убирается обычной кнопкой удаления.
    # is_intern=False добавлен той же строкой для симметрии с
    # available_users_qs — тот же принцип, что уже применён везде по
    # проекту после аудита п. 3.1 (department_page.py/approvals_page.py).
    user = User.objects.filter(id=user_id, is_active=True, is_intern=False).first()

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
    raw_user_id = request.POST.get("user_id")
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        messages.error(request, "Некорректный участник")
        return

    # Владелец проекта обязан оставаться в числе его участников (см.
    # docstring модуля и seed_demo_data.py) — иначе получится нелогичная
    # ситуация "владелец есть, а среди участников — нет". Раньше сравнение
    # шло строками (str(created_by_id) == str(user_id)) — например
    # created_by_id=7 и присланный user_id="007" не совпадали как строки
    # ("7" != "007"), хотя filter(user_id="007") в Django прекрасно
    # приводит "007" к int и находит ту же самую запись — то есть проверку
    # можно было обойти, прислав ID владельца в чуть другом текстовом виде,
    # а сам delete всё равно удалял владельца из участников (аудит, п. 2.3).
    # Сравнение и сам delete теперь используют один и тот же int.
    if project.created_by_id == user_id:
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

    # select_related("department") — раньше не было, добавлен вместе с
    # фильтром по отделу в диалоге "Добавить участника" (см. docstring
    # ниже у available_users): без него department.name на каждого
    # доступного пользователя бил бы отдельным запросом в цикле.
    # is_intern=False — согласовано с matrix_page.py/ask_page.py/
    # department_page.py/approvals_page.py (аудит, п. 3.1): раньше
    # практиканта можно было добавить в проект через этот же список
    # кандидатов, хотя точно такой же список в ask_page.py/reserve_page.py
    # практикантов либо исключает, либо выделяет отдельной категорией.
    available_users_qs = (
        User.objects.filter(is_active=True, is_intern=False)
        .exclude(id__in=UserProject.objects.filter(project_id=project.id).values_list("user_id", flat=True))
        .select_related("department")
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
        # Раньше в шаблон уходил голый queryset и в "Добавить участника"
        # показывалось только ФИО — по запросу добавлена возможность найти
        # человека из ДРУГОГО отдела по должности (например "знаю, что он
        # из DevOps, но нужна конкретная должность"), поэтому теперь у
        # каждого кандидата в разметке видна и должность, и отдел (для
        # клиентского фильтра "Отдел" рядом, см. project.html/extra_js).
        # Никакого нового поля не заводим — это уже существующие
        # User.position/User.department, просто показаны в этом диалоге.
        "available_users": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "position": u.position or "",
                "department": u.department.name if u.department_id else "",
            }
            for u in available_users_qs
        ],
        "departments": Department.objects.order_by("name"),
    }
    return render(request, "project.html", context)
