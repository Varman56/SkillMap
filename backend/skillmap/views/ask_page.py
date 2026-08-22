"""/ask/ — HTML-страница «Кого спросить?», БЕЗ DRF.

Поиск сотрудников по названию навыка (только по самому навыку — раньше
матчило ещё и по названию его подкатегории/категории, но это путало: в
карточке подписано "Совпавшие навыки", а там оказывались навыки, которые
сам текст запроса не содержал вообще — просто потому что их категория
содержала запрошенную подстроку). Результаты группируются по
максимальному уровню владения найденным навыком (у одного user может
совпасть несколько skills, берём лучший).

Учитываются ТОЛЬКО подтверждённые навыки (is_approved=True, см.
_build_employees) — заявки на рассмотрении сюда не идут вовсе: пока
навык не подтверждён HR/руководителем, рекомендовать по нему человека
как знатока преждевременно.

По запросу (тот же приём, что уже сделан в matrix_page.py/matrix.html и
reserve_page.py/reserve.html) фильтрация ЦЕЛИКОМ ПЕРЕНЕСЕНА НА КЛИЕНТ:
раньше поиск по навыку и фильтр отдела были GET-параметрами
(?skill=...&department=...), каждый ввод/выбор — новый запрос и
перезагрузка страницы. Теперь сервер один раз отдаёт данные (см.
_build_employees) — навыки каждого сотрудника кладутся в json_script в
ask.html, — а весь поиск/группировка по уровню считается в JS (см.
extra_js в ask.html), без единого запроса к серверу.

Отдел — фильтр доступен как выпадающий список у HR и Manager (могут
выбрать любой отдел или оставить "Все отделы"); у Employee поле
по-прежнему залочено на его собственный отдел — тот же приём (замок в
UI + принудительная подстановка на бэкенде), что и в reserve_page.py, см.
_resolve_department. Раньше Manager был залочен так же, как Employee —
по запросу лок для Manager сняли: искать консультанта по навыку часто
нужно и за пределами своего отдела, а сами навыки здесь и так только
подтверждённые (see _build_employees), утечки чувствительных данных нет.
ВАЖНО: залоченность Employee — это не только UI-приличие, а единственная
граница приватности данных здесь: залоченная роль получает в
_build_employees СТРОГО сотрудников своего отдела (department_scope),
никогда весь список — иначе фильтрация целиком на клиенте означала бы,
что чужие отделы физически лежат в HTML-странице Employee, просто
визуально скрыты фильтром. У HR и Manager отдел выбирается уже на клиенте
(без перезагрузки), поэтому они получают данные сразу по всем отделам —
для них это и так не секрет (Manager видит все отделы и на ask.html,
хотя на matrix.html и reserve.html он по-прежнему залочен на свой —
это НЕ менялось, см. matrix_page.py/reserve_page.py).

Доступ: любой авторизованный.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from api.models import Department, User

# Заголовки групп по уровню + CSS-класс индикатора — раньше собирались в
# Python (LEVEL_GROUP_LABELS/PROFILE_LEVEL_LABELS_EN из profile_page.py) и
# подставлялись в уже готовый HTML. Теперь группировка происходит в JS (см.
# extra_js в ask.html), поэтому те же самые значения задублированы там же,
# в виде литерального JS-объекта — источник истины для уровней 1-4 всё
# равно profile_page.py (PROFILE_LEVEL_LABELS/PROFILE_LEVEL_LABELS_EN),
# при изменении шкалы уровней нужно поправить оба места.

# Минимальная длина запроса — раньше была 2: старый поиск матчил ещё и
# название категории/подкатегории навыка, и 1 символ там давал слишком
# широкий результат. Теперь ищем строго по названию самого навыка (см.
# docstring модуля), эта причина отпала — по запросу вернули 1. Порог
# проверяется в JS (см. extra_js в ask.html), но константа остаётся
# здесь и уходит в контекст шаблона — единственный источник этого числа.
MIN_SEARCH_LENGTH = 1


def _resolve_department(request) -> tuple[str, bool]:
    """Возвращает (имя_отдела_для_фильтра, редактируем_ли_фильтр_на_странице).

    HR и Manager могут выбрать любой отдел через ?department= (пустое
    значение — "Все отделы", без ограничения) — по запросу лок для
    Manager здесь сняли (было так же, как у Employee). Employee
    по-прежнему всегда видит только свой отдел — фильтр залочен (замок в
    UI) и здесь же принудительно подставляется его primary_department,
    даже если в query string прислано что-то другое: иначе ограничение
    легко обойти, просто исправив URL в адресной строке. ВАЖНО: это
    изменение — только для ask_page.py/ask.html; матрица (matrix_page.py)
    и кадровый резерв (reserve_page.py) держат Manager залоченным на свой
    отдел, как и раньше — это отдельные, не связанные друг с другом
    проверки, трогать их не просили.
    """
    if request.user.has_role("HR", "Manager"):
        return (request.GET.get("department") or "").strip(), True
    return request.user.primary_department, False


def _build_employees(department_scope):
    """Все сотрудники (is_active=True) в рамках department_scope, с их
    навыками — данные для полностью клиентского поиска в ask.html.

    department_scope: None — без ограничения (HR, получает вообще всех,
    выбор отдела дальше происходит на клиенте); "" — не-HR без назначенного
    отдела, искать буквально некого; непустая строка — только этот отдел
    (Manager/Employee всегда залочены на свой, см. _resolve_department).
    """
    if department_scope is not None and not department_scope:
        return []

    # is_active=True — исключает уволенных (см. докстринг User.is_active),
    # is_intern=False — исключает практикантов (тот же приём, что и в
    # matrix_page.py). Это единственная функция, строящая employees для
    # ask.html — фильтр здесь действует на весь payload сразу, поэтому
    # ни практикант, ни уволенный не попадут ни в поиск, ни в группировку
    # по уровню, ни в какой-либо другой разрез этой страницы.
    users_qs = (
        User.objects.filter(is_active=True, is_intern=False)
        .select_related("department")
        .prefetch_related("user_skills__skill")
        .order_by("full_name")
    )
    if department_scope:
        users_qs = users_qs.filter(department__name=department_scope)

    employees = []
    for user in users_qs:
        # is_approved=True — только ПОДТВЕРЖДЁННЫЕ навыки (заявки на
        # рассмотрении, is_approved=False, сюда не попадают вовсе). У
        # одного навыка может быть до 2 строк одновременно — подтверждённая
        # и заявка (см. docstring UserSkill/profile_page.py) — рекомендовать
        # человека как знатока навыка, который ещё не подтверждён HR/
        # руководителем, значит вводить в заблуждение того, кто спрашивает.
        skills = [
            {"skill": us.skill.name, "level": us.level}
            for us in user.user_skills.all()
            if us.skill.is_active and us.is_approved
        ]
        if not skills:
            # Без единого навыка сотрудник никогда не попадёт ни в один
            # результат поиска — не тащим его в payload вообще.
            continue
        employees.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "position": user.position or "",
                "department": user.department.name if user.department_id else "",
                "photo": user.photo,
                "skills": skills,
                # id для {% json_script %} в шаблоне — тот же приём, что и в
                # reserve.html (skills_json_id).
                "skills_json_id": f"ask-skills-{user.id}",
            }
        )
    return employees


@login_required(login_url="/login/")
def ask_page(request):
    department_filter, department_editable = _resolve_department(request)
    # department_scope для _build_employees: None — без ограничения (HR),
    # "" — искать некого (не-HR без назначенного отдела), непустая строка —
    # ограничить этим отделом. У HR фильтр редактируется на клиенте без
    # перезагрузки, поэтому для HR department_scope всегда None — даже если
    # он до этого выбрал конкретный отдел (department_filter здесь — только
    # для того, чтобы select в разметке открылся с уже выбранным значением).
    department_scope = None if department_editable else department_filter

    context = {
        "min_search_length": MIN_SEARCH_LENGTH,
        "department_filter": department_filter,
        "department_editable": department_editable,
        "departments": Department.objects.order_by("name"),
        "employees": _build_employees(department_scope),
    }
    return render(request, "ask.html", context)
