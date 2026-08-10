"""/approvals/ — HTML-страница «Подтверждение навыков», БЕЗ DRF.

Список навыков, которые сотрудники сами добавили себе или изменили уровень
(UserSkill.is_approved=False) — они ждут решения HR/Manager. Модель данных
здесь простая, без раздвоения на «подтверждённую» и «неподтверждённую»
строки: у пары (user, skill) ровно одна запись UserSkill с полями level
и is_approved. Пока is_approved=False — навык считается заявкой на
рассмотрении (см. profile_page.py — там же он выставляется в False при
любом добавлении/изменении уровня).

Подтверждение — не обязательно согласие с тем уровнем, который попросил
сотрудник: HR/Manager сам выбирает, какой уровень зафиксировать (например,
сотрудник указал Docker 4, а подтверждают Docker 3), поэтому в форме
подтверждения есть выбор уровня, а не просто кнопка «Да».

Доступ: только HR и Manager, остальных отправляем в их профиль (тот же
приём, что и в ask_page.py). Manager видит и может подтверждать только
заявки сотрудников своего отдела; HR — заявки всех отделов без исключения.

Всё управляется через GET-фильтры + один POST-экшн:
  ?employee=...   — поиск по ФИО (подстрока, без учёта регистра)
  ?skill=...      — поиск по названию навыка (подстрока, без учёта регистра)
  ?page=...       — номер страницы списка
  POST action=approve_skill, user_skill_id=<id>, level=<1..4>
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from ..models import UserSkill
from .profile_page import PROFILE_LEVEL_LABELS, PROFILE_LEVEL_LABELS_EN, VALID_LEVELS, _parse_level

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

    if not approver.has_role("HR") and pending.user.primary_department != approver.primary_department:
        # Даже если Manager руками подставит чужой id заявки в форму —
        # права всё равно проверяются здесь, а не только скрытием кнопки в UI.
        messages.error(request, "Недостаточно прав: сотрудник не из вашего отдела")
        return

    level = _parse_level(request.POST.get("level"))
    if level is None:
        messages.error(request, "Уровень должен быть от 1 до 4")
        return

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

    pending_qs = (
        UserSkill.objects.filter(is_approved=False)
        .select_related("user", "skill")
        .order_by("-created_at")
    )

    if not request.user.has_role("HR"):
        own_department = request.user.primary_department
        pending_qs = (
            pending_qs.filter(user__departments__name=own_department)
            if own_department
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

    context = {
        "waiting_employee_count": waiting_employee_count,
        "requests": [
            {
                "id": us.id,
                "full_name": us.user.full_name,
                "position": us.user.position,
                "skill_name": us.skill.name,
                "requested_level": us.level,
                "requested_level_label": PROFILE_LEVEL_LABELS.get(us.level, us.level),
                "requested_level_class": PROFILE_LEVEL_LABELS_EN.get(us.level, us.level),
                "submitted_at": us.created_at,
            }
            for us in page_obj
        ],
        "level_options": [(level, PROFILE_LEVEL_LABELS[level]) for level in sorted(VALID_LEVELS)],
        "page_obj": page_obj,
        "employee_search": employee_search,
        "skill_search": skill_search,
    }
    return render(request, "approvals.html", context)
