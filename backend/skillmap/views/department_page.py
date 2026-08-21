"""/my-department/ — HTML-страница «Мой отдел» для Manager, БЕЗ DRF.

Дашборд-сводка по СВОЕМУ отделу (department = request.user.department):
топ-5 навыков отдела, топ-5 редких навыков, распределение уровней (донат),
навыки с разрывом (дефицит экспертов, топ-3), список сотрудников отдела с
поиском, список проектов отдела с поиском.

Раньше здесь была кнопка "Добавить практиканта"/"Добавить сотрудника" —
по запросу пользователя убрана полностью (и с фронта, и с бэка): решение о
том, как в приложение вообще попадают новые пользователи (HR отдельной
фичей, синхронизация с Yandex 360/Zulip API), пока не принято, поэтому
здесь эта форма не нужна вообще, а не временно спрятана.

Доступ: только Manager (см. _can_view) — HR/Employee отправляются в свой
профиль, тот же приём, что и в approvals_page.py/reserve_page.py. У HR нет
одного "своего" отдела (HR видит все), поэтому "Мой отдел" осмысленен
только для Manager — как и на approvals_page.py, роль HR тут ничего не даёт.

По запросу пункт "Подтверждение навыков" убран из общего хедера сайта
(см. base.html) — вместо него в шапке карточки "Сотрудники отдела" здесь
теперь две пилюли: "Сотрудников: N" (раньше была отдельной стат-строкой
над рядом из 4 карточек) и, если есть кого подтверждать, кликабельная
"N сотрудников ожидают подтверждения" — ссылка на /approvals/ (раньше
была отдельным стат-блоком прямо на approvals_page.py). См.
_waiting_employee_count/_waiting_employees_label ниже и dept-header-stats
в department.html/department.css.

ИНТЕРПРЕТАЦИЯ МАКЕТА (важно, если что-то будет казаться не тем числом):
дизайн-макет был нарисован под шкалу уровней 1-5 и абстрактный набор
навыков ("IaC", "Анализ данных" и т.д.), которых нет в реальном каталоге
данных этого проекта. Здесь всё пересчитано под реальную модель:

- Шкала уровней в проекте — 1..4 (см. UserSkill.level), не 1..5.
- "Топ-5/Топ-5 редких" — считаются по РЕАЛЬНЫМ Skill из каталога,
  которые хотя бы у одного сотрудника отдела подтверждены (is_approved).
  Изначально по макету было "Топ-10", но по запросу сокращено до 5, чтобы
  верхний ряд из 4 карточек помещался на экран без прокрутки страницы.
- Донат "Распределение уровней" — считает ТОЛЬКО подтверждённые строки
  UserSkill (is_approved=True), заявки на рассмотрении в статистику не
  входят вообще (бакета "Нет данных" больше нет) — см. docstring
  _level_distribution() и раздел аудита про этот дашборд.
- "Навыки с разрывом" — навыки, где подтверждённых новичков (уровень 1)
  заметно больше, чем подтверждённых экспертов (уровень 4), см.
  _skills_with_gap. Показываются только 3 самых острых (GAP_SKILLS_COUNT) —
  та же причина, что и с "Топ-5" выше: чтобы карточка не была выше соседних
  и весь верхний ряд помещался без прокрутки.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from api.models import Project, User, UserProject, UserSkill
from .project_page import DEFAULT_STATUS, STATUS_META

MIN_LEVEL = 1
MAX_LEVEL = 4
TOP_SKILLS_COUNT = 5  # в макете было 10 — сокращено по запросу, см. docstring модуля
RARE_SKILLS_COUNT = 5
GAP_SKILLS_COUNT = 3  # в макете было 5 — сокращено по запросу, см. docstring модуля
PROJECT_AVATAR_COUNT = 3


def _can_view(user) -> bool:
    return user.has_role("Manager")


def _handle_create_project(request):
    """POST-обработчик кнопки "+" в шапке карточки "Проекты отдела" —
    создаёт новый проект от имени текущего Manager прямо с "Мой отдел",
    без похода на отдельную страницу создания (её и не существует).

    Отдел проекту НЕ назначается явным полем — у Project такого поля нет
    вообще (см. docstring projects_page.py: единственный способ определить
    "чей" проект — created_by.department, то есть отдел ВЛАДЕЛЬЦА). Раз
    created_by=request.user, а _can_view уже гарантирует, что это Manager,
    новый проект автоматически окажется "проектом" именно ЭТОГО отдела —
    ровно то поведение, которое просили ("отдел приписывается как отдел
    руководителя"), без отдельного select'а с отделами в диалоге.

    Владелец сразу же добавляется в участники — тот же инвариант, что и в
    seed_demo_data.py/_handle_remove_member (project_page.py): владелец
    проекта всегда является и его участником, иначе "Нельзя удалить
    владельца проекта из участников" в _handle_remove_member был бы уже
    невозможным состоянием с самого создания. Следом — все кандидаты,
    отмеченные галочками в диалоге (может быть ноль — участников можно
    добрать и потом со страницы самого проекта).
    """
    if not request.user.department_id:
        # Структурно недостижимо через саму кнопку — карточка "Проекты
        # отдела" целиком внутри {% if department %} в department.html, у
        # Manager без отдела эта ветка вообще не рендерится (см.
        # department_page() ниже). Проверка здесь — страховка на случай
        # прямого POST в обход интерфейса, а не для обычного сценария.
        messages.error(request, "У вас не назначен отдел — создать проект нельзя")
        return redirect("my-department-page")

    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "Название проекта обязательно")
        return redirect("my-department-page")

    # Та же проверка длины, что и в _handle_update_project (project_page.py,
    # аудит п. 4.8) — иначе слишком длинное имя дошло бы необработанным до
    # .create() ниже.
    max_name_length = Project._meta.get_field("name").max_length
    if len(name) > max_name_length:
        messages.error(request, f"Название проекта не должно превышать {max_name_length} символов")
        return redirect("my-department-page")

    # Тихо игнорируем нечисловые/пустые id вместо падения — тот же принцип,
    # что и везде в приложении с пользовательским вводом id (см.
    # _handle_add_member в project_page.py, аудит п. 2.5): чек-боксы в
    # диалоге шлют только валидные id, но сам POST не должен полагаться на
    # это и падать необработанным ValueError на мусорном значении в обход
    # интерфейса.
    member_ids = []
    for raw_id in request.POST.getlist("member_ids"):
        try:
            member_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    with transaction.atomic():
        project = Project.objects.create(
            name=name,
            status=DEFAULT_STATUS,
            created_by=request.user,
        )
        UserProject.objects.get_or_create(
            user=request.user, project=project, defaults={"joined_at": timezone.now()}
        )

        # is_active=True, is_intern=False — та же перепроверка на сервере,
        # что и в _handle_add_member (project_page.py, аудит п. 4.9): список
        # кандидатов в диалоге и так уже отфильтрован (см. candidates в
        # контексте department_page() ниже), но сам POST не должен доверять
        # присланным id без проверки — иначе можно добавить уволенного или
        # практиканта прямым POST в обход диалога.
        valid_members = User.objects.filter(id__in=member_ids, is_active=True, is_intern=False)
        for member in valid_members:
            UserProject.objects.get_or_create(
                user=member, project=project, defaults={"joined_at": timezone.now()}
            )

    messages.success(request, f"Проект «{project.name}» создан")
    return redirect("project-page", project_id=project.id)


def _department_members_qs(department):
    # is_intern=False — согласовано с matrix_page.py/ask_page.py (аудит,
    # п. 3.1): раньше здесь фильтровались только уволенные, поэтому топ-5
    # навыков отдела, топ редких, донат распределения уровней и список
    # сотрудников на "Мой отдел" считались ВКЛЮЧАЯ практикантов, хотя в
    # матрице и "Кого спросить?" решение было их не учитывать. Теперь
    # политика одна и та же везде: практиканты нигде не входят в основную
    # статистику/списки по сотрудникам.
    return User.objects.filter(department=department, is_active=True, is_intern=False)


def _ru_plural(n, one, few, many):
    """Выбирает нужную русскую форму слова по числу n (стандартное
    правило: N%10==1 и N%100!=11 -> one; N%10 в 2..4 и N%100 не в
    12..14 -> few; иначе -> many). Например _ru_plural(21, "заявка",
    "заявки", "заявок") -> "заявка"."""
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return few
    return many


def _waiting_employee_count(member_ids):
    """Сколько РАЗНЫХ сотрудников отдела имеют хотя бы одну заявку на
    подтверждение навыка (UserSkill.is_approved=False) — то же множество
    строк, что видит сам Manager на /approvals/ (см. approvals_page.py),
    просто агрегированное по количеству ЛЮДЕЙ, а не заявок: у одного
    сотрудника заявок может быть несколько, а для подсказки в "Мой отдел"
    нужно "N сотрудников ждут", а не "N заявок ждут". member_ids уже
    отфильтрован по is_active=True (см. _department_members_qs), поэтому
    отдельного фильтра на уволенных здесь не нужно — согласовано с тем,
    что approvals_page.py тоже не показывает заявки уволенных."""
    return (
        UserSkill.objects.filter(user_id__in=member_ids, is_approved=False)
        .values("user_id")
        .distinct()
        .count()
    )


def _waiting_employees_label(count):
    """Готовая подпись для пилюли-кнопки перехода к подтверждению навыков
    в "Мой отдел" (например "3 сотрудника ожидают подтверждения") — со
    склонением, посчитанным в Python (см. _ru_plural), а не в шаблоне:
    у Django template нет встроенного 3-формного русского pluralize."""
    noun = _ru_plural(count, "сотрудник", "сотрудника", "сотрудников")
    verb = "ожидает" if count % 10 == 1 and count % 100 != 11 else "ожидают"
    return f"{count} {noun} {verb} подтверждения"


def _top_and_rare_skills(member_ids):
    """(топ-популярные, топ-редкие) навыки отдела по числу сотрудников с
    ПОДТВЕРЖДЁННЫМ уровнем этого навыка. "Редкие" считаются только среди
    навыков, которые есть хотя бы у одного сотрудника — навык, которого
    ни у кого нет, не "редкий", а просто отсутствующий в отделе."""
    counts = (
        UserSkill.objects.filter(
            user_id__in=member_ids, is_approved=True, skill__is_active=True
        )
        .values("skill__name")
        .annotate(holders=Count("user_id", distinct=True))
    )
    rows = [(row["skill__name"], row["holders"]) for row in counts if row["holders"] > 0]

    top_rows = sorted(rows, key=lambda r: (-r[1], r[0]))[:TOP_SKILLS_COUNT]
    rare_rows = sorted(rows, key=lambda r: (r[1], r[0]))[:RARE_SKILLS_COUNT]

    max_count = top_rows[0][1] if top_rows else 0
    top_skills = []
    for name, count in top_rows:
        pct = round(count / max_count * 100) if max_count else 0
        top_skills.append(
            {
                "name": name,
                "count": count,
                # Голое число, а не готовая CSS-строка: раньше сюда клали
                # "width: {{ pct }}%;" и подставляли его прямо в style="" в
                # шаблоне — визуально это убирало "красное" от линтера в
                # смысле "меньше тегов внутри style", но линтер всё равно
                # ругался на САМ факт шаблонного тега внутри style="" (см.
                # правку ниже — там же общее объяснение). Теперь эта цифра
                # уходит в data-pct, а style выставляет JS в конце шаблона —
                # в HTML-атрибуте style вообще не остаётся Django-тегов.
                "pct": pct,
            }
        )
    # pct считается от МАКСИМУМА СРЕДИ САМИХ rare_rows (а не от max_count
    # топ-списка) — иначе почти все столбцы редких навыков были бы
    # микроскопическими (они по определению малочисленны на фоне топ-1) и
    # список превратился бы в ряд еле заметных полосок. Со своим масштабом
    # видна относительная разница внутри самой пятёрки редких — тот же
    # компонент "полоски-бары" (.dept-skill-bars), что и у топ-5, просто со
    # своей осью — по запросу оба списка теперь в одном визуальном стиле
    # (см. department.html/department.css).
    rare_max = rare_rows[-1][1] if rare_rows else 0
    rare_skills = [
        {"name": name, "count": count, "pct": round(count / rare_max * 100) if rare_max else 0}
        for name, count in rare_rows
    ]
    return top_skills, rare_skills


def _level_distribution(member_ids):
    """Разбивка навыков сотрудников отдела на 3 корзины для доната.

    РЕШЕНО (см. audit, было открытым вопросом, зафиксирован финальный
    вариант): считаются ТОЛЬКО подтверждённые строки (is_approved=True).
    Заявки на рассмотрении (is_approved=False) в статистику не попадают
    вообще, поэтому корзины/бакета "Нет данных" в донате больше нет.

    Почему так: у пары (сотрудник, навык) в UserSkill может быть до 2 строк
    одновременно — подтверждённая и заявка на рассмотрении (см. п. 1.2
    аудита, unique_together=(user, skill, is_approved)). Раньше здесь
    считалась КАЖДАЯ строка отдельно (включая заявки), из-за чего было не
    очевидно, что именно понимается под "Нет данных", и пары с обеими
    строками задваивали total. Промежуточный вариант дедуплицировал пары и
    брал максимум из двух уровней, но и он оставлял открытым вопрос, что
    именно считать "данными". По итоговому решению — проще и однозначнее:
    раз подтверждение — это единственный факт, которому можно доверять,
    донат строится ТОЛЬКО по нему. Так как на пару (user, skill) физически
    не может быть больше одной подтверждённой строки (то же
    unique_together), дублирования тут в принципе быть не может — доп.
    дедупликация не нужна.
    """
    rows = UserSkill.objects.filter(user_id__in=member_ids, is_approved=True).values("level")

    high = medium = low = 0
    for row in rows:
        if row["level"] == MAX_LEVEL:
            high += 1
        elif row["level"] == MIN_LEVEL:
            low += 1
        else:
            medium += 1

    total = high + medium + low

    def _bucket(count):
        return {"count": count, "pct": round(count / total * 100) if total else 0}

    high_bucket, medium_bucket, low_bucket = _bucket(high), _bucket(medium), _bucket(low)
    high_end = high_bucket["pct"]
    medium_end = high_end + medium_bucket["pct"]

    return {
        "total": total,
        "high": high_bucket,
        "medium": medium_bucket,
        "low": low_bucket,
        # Границы (в %) между секторами доната для conic-gradient(). Голые
        # числа, а не готовая CSS-строка — style в шаблоне собирает JS из
        # data-атрибутов, без единого Django-тега внутри style="" (см.
        # комментарий у "pct" чуть выше и <script> в department.html).
        # low_end не нужен отдельно — последний сектор всегда идёт до 100%.
        "high_end": high_end,
        "medium_end": medium_end,
    }


def _skills_with_gap(member_ids):
    """Навыки, где подтверждённых новичков (уровень MIN_LEVEL) заметно
    больше, чем подтверждённых экспертов (уровень MAX_LEVEL) — сигнал,
    что отдел рискует остаться без внутренней экспертизы по этому навыку,
    если единственный эксперт уйдёт/сменит проект. Дефицит:
    "высокий" — подтверждённых экспертов нет вообще, хотя новички есть;
    "средний" — эксперты есть, но новичков минимум в полтора раза больше.
    Навыки без такого разрыва в список не попадают."""
    counts = (
        UserSkill.objects.filter(
            user_id__in=member_ids, is_approved=True, level__in=(MIN_LEVEL, MAX_LEVEL)
        )
        .values("skill__name", "level")
        .annotate(cnt=Count("id"))
    )

    by_skill = {}
    for row in counts:
        entry = by_skill.setdefault(row["skill__name"], {"novices": 0, "experts": 0})
        if row["level"] == MIN_LEVEL:
            entry["novices"] = row["cnt"]
        else:
            entry["experts"] = row["cnt"]

    gaps = []
    for name, data in by_skill.items():
        novices, experts = data["novices"], data["experts"]
        if novices == 0:
            continue
        if experts == 0:
            severity = "высокий"
        elif novices >= experts * 1.5:
            severity = "средний"
        else:
            continue
        gaps.append({"name": name, "novices": novices, "experts": experts, "severity": severity})

    severity_rank = {"высокий": 0, "средний": 1}
    gaps.sort(key=lambda g: (severity_rank[g["severity"]], -g["novices"], g["name"]))
    return gaps[:GAP_SKILLS_COUNT]


def _empty_context():
    return {
        "department": None,
        "member_count": 0,
        "employees": [],
        "projects": [],
        "top_skills": [],
        "rare_skills": [],
        "level_distribution": _level_distribution([]),
        "skill_gaps": [],
        "waiting_employee_count": 0,
        "waiting_employees_label": "",
        # Шаблон в ветке "нет отдела" сам фильтр не рендерит (см.
        # department.html), но контекст держим одинаковым по набору ключей
        # с непустой веткой ниже — на случай, если разметка когда-нибудь
        # переедет за пределы {% if department %}.
        "status_choices": [
            {"value": value, "label": meta["label"]}
            for value, meta in STATUS_META.items()
        ],
        "candidates": [],
    }


@login_required(login_url="/login/")
def department_page(request):
    if not _can_view(request.user):
        return redirect("my-profile")

    department = request.user.department

    # Раньше здесь была обработка POST (кнопка "Добавить практиканта") —
    # убрана вместе с самой формой (см. docstring модуля). Теперь POST
    # снова есть — по запросу добавлена кнопка "+" (создать проект прямо с
    # "Мой отдел", см. _handle_create_project) — но это ЕДИНСТВЕННОЕ
    # действие страницы, так что вместо ACTION_HANDLERS-словаря (как в
    # project_page.py/approvals_page.py, где действий несколько) здесь
    # достаточно одной явной проверки action.
    if request.method == "POST":
        if request.POST.get("action") == "create_project":
            return _handle_create_project(request)
        messages.error(request, "Неизвестное действие")
        return redirect("my-department-page")

    if not department:
        # Тот же приём, что и в approvals_page.py/reserve_page.py — Manager
        # без назначенного отдела физически не может увидеть "свой отдел",
        # показываем пустую страницу вместо ошибки.
        return render(request, "department.html", _empty_context())

    # Активные сотрудники (is_active=True) — единственный источник и для
    # статистики по навыкам, и для списка "Сотрудники отдела"/счётчика.
    # is_active=False в этом проекте значит "уволен" (см. seed_demo_data.py
    # / фильтр "Только уволенные" в reserve.html), а не "не активирован" —
    # поэтому уволенных тут не показываем, как и везде в проекте по
    # умолчанию.
    members_qs = _department_members_qs(department).order_by("full_name")
    member_ids = list(members_qs.values_list("id", flat=True))

    top_skills, rare_skills = _top_and_rare_skills(member_ids)

    employees = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "position": u.position or "",
            "photo": u.photo,
        }
        for u in members_qs
    ]

    # Кандидаты в диалог "+ Создать проект" (см. create_project ниже) — по
    # запросу ЛЮБОЙ активный сотрудник компании, а не только этого отдела
    # (проект часто набирают вперемешку из разных отделов, тот же довод,
    # что и у available_users в project_page.py). is_active=True,
    # is_intern=False — согласовано со всем остальным приложением (аудит,
    # п. 3.1). Сам request.user (создающий проект менеджер) исключён из
    # списка — он и так становится участником автоматически (см.
    # _handle_create_project), показывать его же ещё и чек-боксом было бы
    # избыточно/путало бы.
    candidates_qs = (
        User.objects.filter(is_active=True, is_intern=False)
        .exclude(id=request.user.id)
        .select_related("department")
        .order_by("full_name")
    )
    candidates = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "position": u.position or "",
            "department": u.department.name if u.department_id else "",
        }
        for u in candidates_qs
    ]

    # Раньше проект считался "проектом отдела", если в нём есть хотя бы
    # ОДИН участник из отдела (project_users__user_id__in=member_ids) — на
    # практике участники почти всегда набраны вперемешку из разных
    # отделов (см. seed_demo_data.py), поэтому такой фильтр находил почти
    # ВСЕ проекты компании в КАЖДОМ отделе, а не только реально "свои".
    # Теперь — тот же принцип, что и в новой projects_page.py (список
    # "Проекты" для HR): проект относится к отделу его ВЛАДЕЛЬЦА
    # (created_by), а не к отделам его участников. distinct() тоже больше
    # не нужен — created_by это FK (один проект = один владелец), в
    # отличие от project_users, дублей быть не может в принципе.
    projects_qs = (
        Project.objects.filter(created_by__department_id=department.id)
        .order_by("name")
        .prefetch_related("project_users__user")
    )
    projects = []
    for project in projects_qs:
        # is_active — уволенные (см. seed_demo_data.py/reserve_page.py) не
        # попадают в аватарки участников проекта, тем же принципом, что и
        # весь остальной список сотрудников на этой странице. Фильтруем
        # в Python (не в queryset) — project_users уже загружены разом
        # через prefetch_related выше, доп. запроса на проект не будет.
        # Тот же фикс сделан и в project_page.py (список участников самой
        # страницы проекта).
        project_members = [pm for pm in project.project_users.all() if pm.user.is_active]
        visible = project_members[:PROJECT_AVATAR_COUNT]
        # status/status_label/status_css_class — тот же приём и тот же общий
        # источник истины (STATUS_META в project_page.py), что и на странице
        # "Проекты" (projects_page.py): раньше статус проекта здесь вообще
        # не показывался. По запросу добавлен ФИЛЬТР "Статус" рядом с уже
        # существующим поиском (см. deptProjectStatus в department.html) —
        # показать только проекты в конкретном статусе (например только
        # "В работе"), а не сортировка списка. status — сырое значение из
        # БД для сравнения с выбранным пунктом <select> на клиенте,
        # status_label/status_css_class — готовые подпись/класс для пилюли
        # на карточке (без неё фильтр было бы не на что смотреть).
        status_meta = STATUS_META.get(
            project.status, {"label": project.status or "—", "css_class": "unknown"}
        )
        projects.append(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "avatars": [pm.user.photo for pm in visible],
                "extra_count": max(0, len(project_members) - len(visible)),
                "status": project.status,
                "status_label": status_meta["label"],
                "status_css_class": status_meta["css_class"],
            }
        )

    waiting_employee_count = _waiting_employee_count(member_ids)

    context = {
        "department": department,
        "member_count": len(employees),
        "employees": employees,
        "projects": projects,
        # Пункты фильтра "Статус" в карточке "Проекты отдела" (см.
        # deptProjectStatus в department.html) — тот же источник истины
        # STATUS_META, что и на странице "Проекты" (projects_page.py).
        "status_choices": [
            {"value": value, "label": meta["label"]}
            for value, meta in STATUS_META.items()
        ],
        # Кандидаты в диалог "+ Создать проект" (см. candidates_qs выше).
        "candidates": candidates,
        "top_skills": top_skills,
        "rare_skills": rare_skills,
        "level_distribution": _level_distribution(member_ids),
        "skill_gaps": _skills_with_gap(member_ids),
        # Раньше "Сотрудников в отделе: N" была отдельной стат-строкой над
        # рядом из 4 карточек, а "N сотрудников ожидают подтверждения" —
        # отдельным стат-блоком на /approvals/ (см. approvals_page.py) — по
        # запросу оба перенесены сюда, в шапку карточки "Сотрудники отдела"
        # (см. department.html/_waiting_employee_count). Вторая пилюля
        # теперь ещё и кликабельна — ссылка на /approvals/, т.к. сам пункт
        # "Подтверждение навыков" убран из хедера сайта (см. base.html).
        "waiting_employee_count": waiting_employee_count,
        "waiting_employees_label": (
            _waiting_employees_label(waiting_employee_count) if waiting_employee_count else ""
        ),
    }
    return render(request, "department.html", context)
