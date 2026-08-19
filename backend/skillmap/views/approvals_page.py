"""/approvals/ — HTML-страница «Подтверждение навыков», БЕЗ DRF.

Список навыков, которые сотрудники сами добавили себе или изменили уровень
(UserSkill.is_approved=False) — они ждут решения HR/Manager. У пары
(user, skill) может быть до двух строк UserSkill одновременно: уже
подтверждённая (is_approved=True) и заявка на рассмотрении
(is_approved=False, ей и оперирует эта страница) — см. docstring модели
UserSkill в api/models.py.

Подтверждение — не обязательно согласие с тем уровнем, который попросил
сотрудник: HR/Manager сам выбирает, какой уровень зафиксировать (например,
сотрудник указал Docker 4, а подтверждают Docker 3), поэтому в форме
подтверждения есть выбор уровня, а не просто кнопка «Да».

При подтверждении заявки её строка становится подтверждённой на выбранном
уровне, а прежняя подтверждённая строка этого же навыка (если была,
например Docker уже был подтверждён на уровне 2) — удаляется: подтверждена
может быть только одна строка на пару (user, skill), это же гарантирует и
unique_together на модели.

Доступ: только Manager (см. _can_view) — ни HR, ни Employee сюда не
попадают, даже если у пользователя есть ещё и роль HR вдобавок к
Manager: роль HR на этой странице ничего не даёт и не расширяет видимость
по отделам, это осознанное решение (не как на ask_page.py/reserve_page.py,
где HR видит все отделы). Остальных без доступа отправляем в их профиль
(тот же приём, что и в ask_page.py).

Фильтр отдела на странице — всегда залоченное поле (замочек), НЕ
выпадающий список: сюда попадает только Manager, ему нечего выбирать, он
видит только заявки своего отдела — без исключений.

Всё управляется через GET-фильтры + один POST-экшн:
  ?employee=...   — поиск по ФИО (подстрока, без учёта регистра)
  ?skill=...      — поиск по названию навыка (подстрока, без учёта регистра)
  ?sort=asc|desc  — сортировка по дате отправки заявки (по умолчанию desc,
                    т.е. сначала новые — соответствует стрелке ↓ в шапке
                    колонки «Дата отправки» в UI)
  ?page=...       — номер страницы списка
  POST action=approve_skill, user_skill_id=<id>, level=<1..4>
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from api.models import UserSkill
from .profile_page import (
    PROFILE_LEVEL_LABELS,
    PROFILE_LEVEL_LABELS_EN,
    VALID_LEVELS,
    _approved_level,
    _parse_level,
)

PAGE_SIZE = 8


def _can_view(user) -> bool:
    return user.has_role("Manager")


def _handle_approve(request, approver):
    pending = (
        UserSkill.objects.select_related("user", "skill")
        .filter(id=request.POST.get("user_skill_id"), is_approved=False)
        .first()
    )
    if not pending:
        messages.error(request, "Заявка не найдена или уже обработана")
        return

    if pending.user.primary_department != approver.primary_department:
        # Даже если Manager руками подставит чужой id заявки в форму —
        # права всё равно проверяются здесь, а не только скрытием кнопки в UI.
        # Роль HR тут НИЧЕГО не даёт (см. docstring модуля выше) — если
        # у подтверждающего вдобавок к Manager есть роль HR, это не должно
        # позволять подтверждать заявки чужих отделов; раньше здесь было
        # условие "not approver.has_role('HR') and ...", из-за чего HR
        # мог в обход GET-фильтра списка (который честно ограничен своим
        # отделом) подтвердить POST'ом заявку любого чужого отдела.
        messages.error(request, "Недостаточно прав: сотрудник не из вашего отдела")
        return

    if not pending.user.is_active:
        # Та же страховка, что и с отделом чуть выше: список заявок уже
        # не показывает уволенных (см. фильтр user__is_active=True в
        # approvals_page() ниже), но POST может прийти и в обход UI —
        # подтверждать навык уже уволенному сотруднику не имеет смысла.
        messages.error(request, "Сотрудник уволен — подтверждение недоступно")
        return

    level = _parse_level(request.POST.get("level"))
    if level is None:
        messages.error(request, "Уровень должен быть от 1 до 4")
        return

    # Подтверждающий сам выбирает уровень (см. docstring модуля) — но не
    # ниже и не равно уже подтверждённому уровню этого же навыка: тот же
    # инвариант, что и при создании/правке заявки самим сотрудником (см.
    # _approved_level/_handle_add_skill/_handle_update_skill в
    # profile_page.py). Без этой проверки можно было, например, при уже
    # подтверждённом Docker 2 открыть заявку на Docker 3 и сохранить
    # подтверждение на уровне 1 — старая (более высокая и корректная)
    # подтверждённая запись удалялась бы ниже пунктом кода и заменялась
    # на понижающую, что не имеет смысла: подтверждение — это согласие
    # с ростом уровня, а не способ его понизить.
    approved_level = _approved_level(pending.user, pending.skill)
    if approved_level is not None and level <= approved_level:
        messages.error(
            request,
            f"Навык «{pending.skill.name}» ({pending.user.full_name}) уже подтверждён на уровне "
            f"{PROFILE_LEVEL_LABELS[approved_level]} — подтвердить можно только на более высоком уровне",
        )
        return

    # Подтверждена может быть только одна строка на (user, skill) —
    # если уже была подтверждённая заявка этого навыка (например,
    # Docker 2 подтверждён, а сейчас подтверждаем заявку на Docker 4),
    # она удаляется, а её место занимает текущая заявка.
    UserSkill.objects.filter(
        user_id=pending.user_id, skill_id=pending.skill_id, is_approved=True
    ).delete()

    pending.level = level
    pending.is_approved = True
    pending.save(update_fields=["level", "is_approved"])
    messages.success(
        request, f"Навык «{pending.skill.name}» ({pending.user.full_name}) подтверждён на уровне {level}"
    )


@login_required(login_url="/login/")
def approvals_page(request):
    if not _can_view(request.user):
        return redirect("my-profile")

    if request.method == "POST":
        if request.POST.get("action") == "approve_skill":
            _handle_approve(request, request.user)
        else:
            messages.error(request, "Неизвестное действие")
        return redirect("approvals-page")

    employee_search = (request.GET.get("employee") or "").strip()
    skill_search = (request.GET.get("skill") or "").strip()
    sort_dir = "asc" if request.GET.get("sort") == "asc" else "desc"

    pending_qs = (
        UserSkill.objects.filter(is_approved=False, user__is_active=True)
        .select_related("user", "skill")
        .order_by("created_at" if sort_dir == "asc" else "-created_at")
    )
    # user__is_active=True — исключает заявки уволенных сотрудников
    # (is_active=False значит "уволен", см. seed_demo_data.py). Раньше
    # фильтра не было, поэтому руководитель мог увидеть в очереди на
    # подтверждение заявку уже уволенного сотрудника из своего бывшего
    # отдела — несогласованно с "Мой отдел" (department_page.py), где
    # такие сотрудники не считаются.

    # Фильтр отдела здесь не выпадающий, а всегда залоченный (тот же
    # "замочек", что и в ask_page.py/reserve_page.py) — эту страницу
    # открывает только Manager (см. _can_view), выбирать отдел ему
    # незачем, он и так видит только свой. В отличие от ask_page.py/
    # reserve_page.py, роль HR здесь ничего не меняет: даже если она
    # есть у пользователя вдобавок к Manager, отдел всё равно только
    # свой — на этой странице действует роль Manager, а не HR.
    department_filter = request.user.primary_department
    pending_qs = (
        pending_qs.filter(user__department__name=department_filter)
        if department_filter
        else pending_qs.none()
    )

    if employee_search:
        pending_qs = pending_qs.filter(user__full_name__icontains=employee_search)
    if skill_search:
        pending_qs = pending_qs.filter(skill__name__icontains=skill_search)

    pending_qs = pending_qs.distinct()

    waiting_employee_count = pending_qs.values("user_id").distinct().count()

    paginator = Paginator(pending_qs, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Ссылки пагинации/сортировки в шаблоне должны сохранять остальные
    # активные фильтры (employee/skill/sort) — собираем query string без
    # "page" один раз здесь, а не руками в шаблоне (там раньше терялся
    # skill_search при переходе на вторую страницу).
    base_params = request.GET.copy()
    base_params.pop("page", None)
    qs_without_page = base_params.urlencode()

    sort_toggle_params = base_params.copy()
    sort_toggle_params["sort"] = "asc" if sort_dir == "desc" else "desc"
    qs_for_sort_toggle = sort_toggle_params.urlencode()

    def _min_selectable_level(us):
        """Минимальный уровень, который можно выбрать при подтверждении —
        на 1 выше уже подтверждённого уровня этого же навыка, либо общий
        min_level, если подтверждённой строки ещё нет. Используется в
        шаблоне (data-min-selectable у ползунка, см. JS в approvals.html),
        чтобы не дать даже выбрать уровень <= уже подтверждённого.
        Серверная проверка того же самого в _handle_approve — не замена,
        а страховка на случай ручного POST в обход интерфейса."""
        approved_level = _approved_level(us.user, us.skill)
        return approved_level + 1 if approved_level is not None else min(VALID_LEVELS)

    context = {
        "waiting_employee_count": waiting_employee_count,
        "requests": [
            {
                "id": us.id,
                "user_id": us.user_id,
                "full_name": us.user.full_name,
                "position": us.user.position,
                "photo": us.user.photo,
                "skill_name": us.skill.name,
                "requested_level": us.level,
                "requested_level_label": PROFILE_LEVEL_LABELS.get(us.level, us.level),
                "requested_level_class": PROFILE_LEVEL_LABELS_EN.get(us.level, us.level),
                "submitted_at": us.created_at,
                "min_selectable_level": _min_selectable_level(us),
            }
            for us in page_obj
        ],
        "level_options": [(level, PROFILE_LEVEL_LABELS[level]) for level in sorted(VALID_LEVELS)],
        "min_level": min(VALID_LEVELS),
        "max_level": max(VALID_LEVELS),
        "page_obj": page_obj,
        "employee_search": employee_search,
        "skill_search": skill_search,
        "department_filter": department_filter,
        "sort_dir": sort_dir,
        "qs_without_page": qs_without_page,
        "qs_for_sort_toggle": qs_for_sort_toggle,
    }
    return render(request, "approvals.html", context)
