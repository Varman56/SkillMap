"""/projects/ — HTML-страница «Проекты» (список ВСЕХ проектов), БЕЗ DRF.

Отдельная страница от /projects/<id>/ (project_page.py, карточка одного
проекта) — эта служит каталогом/поиском по всем проектам сразу. Сделана
по образцу ask_page.py/ask.html: сервер один раз отдаёт JS вообще все
проекты со всеми данными для поиска/фильтра, дальше поиск по названию/
описанию и фильтр по отделу — целиком на клиенте, без единого запроса к
серверу (см. extra_js в projects.html). В отличие от "Кого спросить?",
здесь результаты видны СРАЗУ при заходе на страницу (весь список, можно
проскроллить) — пустой поиск не прячет список, а просто не сужает его.

Доступ: ТОЛЬКО HR (см. _can_view) — остальных отправляем в их профиль,
тот же приём, что и в reserve_page.py/approvals_page.py. Сама карточка
конкретного проекта (/projects/<id>/) при этом как была доступна любому
авторизованному, так и осталась — ограничение только на этот список.

ОТДЕЛ ДЛЯ ФИЛЬТРА: у Project нет собственного поля "отдел" — участники
(UserProject) могут быть из любых отделов вперемешку, поэтому единственный
однозначный вариант — отдел ВЛАДЕЛЬЦА проекта (Project.created_by.department,
он же тот, кто создал проект в своём отделе). Проекты без владельца
(created_by=None, см. on_delete=SET_NULL в модели) в фильтр по отделу не
попадают ни при каком выборе конкретного отдела — только видны при "Все
отделы".
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render

from api.models import Department, Project
from .project_page import DEFAULT_STATUS, STATUS_META


def _can_view(user) -> bool:
    return user.has_role("HR")


def _build_projects():
    """Все проекты со всеми данными для клиентского поиска/фильтра —
    тот же приём, что и _build_employees в ask_page.py/reserve_page.py.

    member_count считается через annotate (Count по обратной связи
    project_users), а не len(prefetch) — участников может быть много,
    а сам список участников на этой странице не нужен вообще, нужно
    только число.
    """
    projects_qs = (
        Project.objects.select_related("created_by", "created_by__department")
        .annotate(member_count=Count("project_users", distinct=True))
        .order_by("name")
    )

    projects = []
    for project in projects_qs:
        status_meta = STATUS_META.get(
            project.status, {"label": project.status or "—", "css_class": "unknown"}
        )
        owner = project.created_by
        projects.append(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description or "",
                # status — сырое значение из БД (ключ STATUS_META, например
                # "Active"), нужен клиентскому фильтру "Статус" (см. extra_js
                # в projects.html) для точного сравнения с выбранным пунктом
                # <select>, отдельно от status_label (готовая подпись для
                # пилюли на карточке).
                "status": project.status,
                "status_label": status_meta["label"],
                "status_css_class": status_meta["css_class"],
                "owner_name": owner.full_name if owner else "",
                "department": owner.department.name if owner and owner.department_id else "",
                "member_count": project.member_count,
                # Тот же приём "детерминированной, но разной иконки", что и
                # у proj-icons в profile.html — но там random.randint (значит
                # иконка перетасовывается на КАЖДОЙ перезагрузке страницы),
                # здесь осознанно по id, чтобы у одного и того же проекта
                # иконка не "мигала" между заходами HR на страницу списка.
                "icon": f"proj-icons/Project-icon-{(project.id - 1) % 5 + 1}.svg",
            }
        )
    return projects


@login_required(login_url="/login/")
def projects_page(request):
    if not _can_view(request.user):
        return redirect("my-profile")

    context = {
        "projects": _build_projects(),
        "departments": Department.objects.order_by("name"),
        # Пункты фильтра "Статус" — по запросу это именно ФИЛЬТР "показать
        # только тех, кто В работе/Завершён и т.д.", а не сортировка списка
        # (сортировку по названию убрали как лишнюю — список и так стабильно
        # идёт по .order_by("name") из _build_projects()). Тот же порядок
        # пунктов, что и в форме редактирования проекта (project_page.py),
        # один источник истины STATUS_META.
        "status_choices": [
            {"value": value, "label": meta["label"]}
            for value, meta in STATUS_META.items()
        ],
    }
    return render(request, "projects.html", context)
