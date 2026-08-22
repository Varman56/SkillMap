"""/analytics/ — HTML-страница «Аналитика», HR-only, БЕЗ DRF.

Дашборд по ВСЕЙ компании (в отличие от "Мой отдел" — department_page.py,
который считает то же самое, но всегда по department = request.user.
department одного Manager'а): здесь то же самое семейство метрик, но с
опциональным фильтром "Отдел" (?department_id=), который сужает выборку
СОТРУДНИКОВ до одного отдела — без параметра или с department_id="" смысл
"Все отделы" (используются вообще все активные сотрудники компании).

Часть метрик ПОВТОРЯЕТ логику department_page.py почти один в один (топ-
навыки/редкие навыки, донат распределения уровней, разрыв новичков/
экспертов) — так и должно быть, это тот же самый принцип подсчёта, просто
с другим множеством сотрудников на входе (весь фильтр вместо одного
отдела). Копия, а не общая функция в api/helpers.py — здесь этот дашборд
устроен НЕ идентично (другой набор карточек: добавлены категории каталога
и управление навыками, убран разрыв по 3, показывается топ-10 вместо
топ-5) и то, что метрики похожи сегодня, не значит, что их не разведут
дальше — дублирование здесь осознанное, ту же логику см. в докстринге
_top_and_rare_skills ниже.

ИНТЕРПРЕТАЦИЯ МАКЕТА (важно, если что-то будет казаться не тем числом —
макет рисовался абстрактно, без привязки к реальной модели данных):

- Шкала уровней — 1..4 (см. UserSkill.level), не 1..5, как на макете.
  Донат "Распределение уровней" считает ТОЛЬКО подтверждённые строки
  (is_approved=True) — бакета "Нет данных" нет, тот же принцип и то же
  решение, что и в _level_distribution() (department_page.py).
- "Категории навыков" (кластер кругов) — это доля каталога В ЦЕЛОМ
  (сколько РАЗНЫХ активных навыков привязано к категории, из общего
  числа активных навыков в каталоге) — ЭТА карточка НЕ зависит от
  фильтра "Отдел" (в макете подписано "Доля навыков каталога по
  категориям", а каталог один на всю компанию, а не "по отделам").
  Круги считаются и раскладываются в JS (см. analytics.html) —
  Python отдаёт только имя/долю каждой категории.
- "Топ-10 навыков"/"Топ-10 редких навыков" — на макете было "Топ-5
  редких" сначала, затем по запросу расширено до "Топ-10" в том же
  визуальном стиле (полоски), что и топ-10 популярных. Тот же принцип,
  что и в _top_and_rare_skills (department_page.py): считаются только
  активные навыки, у которых есть хотя бы один сотрудник с ПОДТВЕРЖДЁННЫМ
  уровнем (в рамках выбранного фильтра "Отдел") — навык, которого нет ни
  у кого, не "редкий", а просто отсутствующий.
- "Карта разрывов" — на макете были абстрактные строки-"отделы"
  ("Backend-разработка", "QA" и т.д. — таких сущностей нет в модели
  данных вообще). Пересчитано на РЕАЛЬНЫЕ навыки, тот же алгоритм, что и
  _skills_with_gap (department_page.py): "высокий" дефицит — подтверждённых
  экспертов (ур. 4) нет вообще при наличии новичков (ур. 1), "средний" —
  эксперты есть, но новичков минимум в 1.5 раза больше. Третьей ступени
  "низкая" в этом алгоритме нет и на "Мой отдел" тоже не было — в макете
  она была декоративной, без реальной сигнальной ценности (все навыки без
  выраженного перекоса просто не попадают в список, это НЕ то же самое,
  что "низкая срочность"). Показываются GAP_SKILLS_COUNT самых острых
  вместо жёсткого списка из макета.
- "Навыков подтверждено" (стат-пилюля) — доля УНИКАЛЬНЫХ пар
  (сотрудник, навык) в выбранной области, у которых есть подтверждённая
  строка, от всех уникальных пар (подтверждённых И на рассмотрении) — это
  метрики нет ни в одном макете буквально, введена как осмысленный аналог
  подписи "Навыков подтверждено 89%".
- "Сотрудников" (стат-пилюля) — по запросу стала кликабельной: раскрывает
  выпадающий список ФИО/должности КОНКРЕТНО тех людей, что вошли в
  member_count (тот же member_ids/тот же фильтр "Отдел", что и во всех
  остальных карточках) — см. `members` в контексте и .an-members-dropdown
  в analytics.html. Раньше число можно было увидеть, а состав — только
  уйдя на другую страницу.

УПРАВЛЕНИЕ НАВЫКАМИ (кнопка "+" на пилюле "Навыков в каталоге", диалог
см. analytics.html) — единственное место в проекте, где HR может завести
СОВСЕМ НОВЫЙ Skill (до этого Skill можно было только назначить
пользователю, а сам каталог наполнялся исключительно seed_demo_data).
Добавление навыка одновременно может завести новую категорию/подкатегорию
"по месту" — см. _handle_add_skill: в диалоге по запросу можно выбрать
category_id/subcategory_id из уже существующих ИЛИ вписать оба текстом
("+ Новая категория…" — тогда подкатегория тоже обязана быть новой, у
свежесозданной категории просто не может быть готовых подкатегорий).
"Удаление" навыка — МЯГКОЕ (is_active=False), не DELETE: у Skill везде в
проекте RESTRICT на FK (SubcategorySkill.skill, UserSkill.skill, см.
api/models.py) — попытка жёстко удалить навык, который уже кому-то
назначен или к чему-то привязан, упала бы ProtectedError. is_active уже
и так единственный переключатель видимости навыка везде в проекте
(build_skills_cascade_data/matrix_page.py/ask_page.py/profile_page.py
фильтруют по нему) — переиспользуем его же, а не добавляем новое поле.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect, render

from api.models import (
    Category,
    CategorySubcategory,
    Department,
    Skill,
    Subcategory,
    SubcategorySkill,
    User,
    UserSkill,
)

MIN_LEVEL = 1
MAX_LEVEL = 4
TOP_SKILLS_COUNT = 10
RARE_SKILLS_COUNT = 10
# Раньше жёстко резалось до 6 — карточка показывала только самые острые
# разрывы, без способа увидеть остальное. Теперь фронтенд (analytics.html)
# сам сворачивает список визуально (первые несколько строк + кнопка
# "Показать все" с прокруткой) — бэкенду достаточно отдать разумный
# верхний потолок вместо реального лимита. 30 практически никогда не
# достижимо (навыков с разрывом не может быть больше, чем навыков в
# каталоге вообще, а каталог — 16 навыков в демоданных), это просто
# защита от вырожденного случая, если каталог сильно вырастет.
GAP_SKILLS_COUNT = 30


def _can_view(user) -> bool:
    return user.has_role("HR")


def _ru_plural(n, one, few, many):
    """Копия _ru_plural (department_page.py) — обычное правило русского
    склонения по числу (N%10==1 и N%100!=11 -> one; 2..4/не 12..14 ->
    few; иначе -> many). Нужна для подписи "Каталог — N навыков" в
    диалоге "Управление навыками" (см. analytics.html) — своя копия по
    той же причине, что и остальное дублирование в этом модуле (см.
    докстринг модуля)."""
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return few
    return many


def _scope_users_qs(department):
    """Те же два фильтра, что и _department_members_qs (department_page.py):
    is_active=True (не уволен), is_intern=False (стажёры нигде в основной
    статистике не участвуют, аудит п. 3.1) — здесь просто с ОПЦИОНАЛЬНЫМ
    отделом вместо всегда одного department = request.user.department."""
    qs = User.objects.filter(is_active=True, is_intern=False)
    if department is not None:
        qs = qs.filter(department=department)
    return qs


def _top_and_rare_skills(member_ids):
    """Копия _top_and_rare_skills (department_page.py) — см. докстринг
    модуля, почему это отдельная копия, а не общая функция."""
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
    top_skills = [
        {"name": name, "count": count, "pct": round(count / max_count * 100) if max_count else 0}
        for name, count in top_rows
    ]
    # pct у редких — от максимума СРЕДИ САМИХ редких (не от топ-1) — та же
    # причина, что и в department_page.py: иначе почти все полоски были бы
    # микроскопическими на фоне самого популярного навыка компании.
    rare_max = rare_rows[-1][1] if rare_rows else 0
    rare_skills = [
        {"name": name, "count": count, "pct": round(count / rare_max * 100) if rare_max else 0}
        for name, count in rare_rows
    ]
    return top_skills, rare_skills


def _level_distribution(member_ids):
    """Копия _level_distribution (department_page.py) — см. докстринг
    модуля."""
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
        "high_end": high_end,
        "medium_end": medium_end,
    }


def _skills_with_gap(member_ids):
    """Копия _skills_with_gap (department_page.py, см. докстринг там же
    про смысл "высокий"/"средний") — с одним отличием: fill_pct добавлен
    для полоски-визуализации карты разрывов на этой странице (доля
    подтверждённых экспертов среди подтверждённых новичков+экспертов —
    чем короче и краснее полоска, тем острее дефицит, см. analytics.html)."""
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
        fill_pct = round(experts / (novices + experts) * 100)
        gaps.append({
            "name": name, "novices": novices, "experts": experts,
            "severity": severity, "fill_pct": fill_pct,
        })

    severity_rank = {"высокий": 0, "средний": 1}
    gaps.sort(key=lambda g: (severity_rank[g["severity"]], -g["novices"], g["name"]))
    return gaps[:GAP_SKILLS_COUNT]


def _confirmation_rate(member_ids):
    """Доля УНИКАЛЬНЫХ пар (сотрудник, навык) с подтверждённой строкой от
    всех уникальных пар (подтверждённых И на рассмотрении вместе) — см.
    докстринг модуля, "Навыков подтверждено" в стат-пилюле."""
    pairs_qs = UserSkill.objects.filter(user_id__in=member_ids)
    total_pairs = pairs_qs.values("user_id", "skill_id").distinct().count()
    if not total_pairs:
        return 0
    approved_pairs = (
        pairs_qs.filter(is_approved=True).values("user_id", "skill_id").distinct().count()
    )
    return round(approved_pairs / total_pairs * 100)


def _category_shares():
    """(имя категории, доля % от каталога, штук) для кластера кругов —
    см. докстринг модуля: доля от ВСЕГО активного каталога, без фильтра
    по отделу. Категория без единого активного навыка в список не
    попадает (круг был бы нулевого размера — бессмысленно).

    ВАЖНО про сами числа: Category<->Subcategory — M2M (см. api/models.py),
    а seed_demo_data.py заводит Subcategory через get_or_create(name=...)
    БЕЗ привязки к конкретной категории — на практике это означает, что
    одна и та же подкатегория ("Языки программирования",
    "Библиотеки/Фреймворки") оказывается общей сразу для Backend и
    Frontend, и Python/Django/FastAPI/JavaScript/TypeScript/React/Vue.js
    транзитивно относятся к ОБЕИМ категориям одновременно — это не баг
    здесь, а как есть в реальных данных этой схемы. Навык, у которого
    несколько категорий, засчитывается КАЖДОЙ из них ДРОБНО (1/N) —
    иначе (а первая попытка была именно такой, через skill_category_map)
    один "первый" категории забирал бы себе всё, а остальные обнулялись
    — с дробным распределением сумма долей корректно даёт ~100% каталога,
    как и обещает подпись карточки "Доля навыков каталога по категориям".
    values_list(...).distinct() ЗДЕСЬ безопасен (в отличие от более ранней
    версии через Category.objects.annotate(Count(...)) с фильтром по тому
    же M2M-пути — та завышала счётчик из-за фан-аута JOIN'а): тут нет
    агрегации в SQL вообще, просто плоские пары (категория, skill_id) и
    обычный DISTINCT, дедуплицирующий их как есть."""
    active_skill_ids = set(Skill.objects.filter(is_active=True).values_list("id", flat=True))
    total = len(active_skill_ids)
    if not total:
        return []

    rows = (
        Category.objects.filter(subcategories__skills__id__in=active_skill_ids)
        .values_list("name", "subcategories__skills__id")
        .distinct()
    )
    skill_categories: dict[int, set] = {}
    for category_name, skill_id in rows:
        skill_categories.setdefault(skill_id, set()).add(category_name)

    fractional_counts: dict[str, float] = {}
    for skill_id, names in skill_categories.items():
        share = 1 / len(names)
        for name in names:
            fractional_counts[name] = fractional_counts.get(name, 0) + share

    shares = [
        {"name": name, "count": round(count), "pct": round(count / total * 100, 1)}
        for name, count in fractional_counts.items()
    ]
    shares.sort(key=lambda r: (-r["pct"], r["name"]))
    return shares


def _skills_catalog_for_dialog():
    """Каталог для диалога «Управление навыками», сгруппированный по
    категории (первая найденная — см. skill_category_name в api/helpers.py:
    тот же приём, скилл в этом каталоге почти всегда привязан ровно к
    одной категории через одну подкатегорию, показывать все возможные —
    не нужно)."""
    from api.helpers import skill_category_name

    skills_qs = (
        Skill.objects.filter(is_active=True)
        .prefetch_related("subcategories__categories")
        .order_by("name")
    )
    grouped: dict[str, list[dict]] = {}
    for skill in skills_qs:
        subcategory = skill.subcategories.first()
        category = subcategory.categories.first() if subcategory else None
        category_name = category.name if category else "Без категории"
        grouped.setdefault(category_name, []).append({
            "id": skill.id,
            "name": skill.name,
            "subcategory": subcategory.name if subcategory else "",
        })
    return [
        {"category": name, "skills": items}
        for name, items in sorted(grouped.items())
    ]


def _handle_add_skill(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "Название навыка обязательно")
        return

    max_name_length = Skill._meta.get_field("name").max_length
    if len(name) > max_name_length:
        messages.error(request, f"Название навыка не должно превышать {max_name_length} символов")
        return

    new_category_name = (request.POST.get("new_category_name") or "").strip()
    new_subcategory_name = (request.POST.get("new_subcategory_name") or "").strip()
    category_id = request.POST.get("category_id") or None
    subcategory_id = request.POST.get("subcategory_id") or None

    with transaction.atomic():
        if new_category_name:
            # Та же casefold()-проверка дублей без учёта регистра, что и
            # у отделов (_handle_create_department в reserve_page.py) —
            # по той же причине (SQLite LIKE не сворачивает кириллицу).
            existing = {c.casefold() for c in Category.objects.values_list("name", flat=True)}
            if new_category_name.casefold() in existing:
                messages.error(request, f"Категория «{new_category_name}» уже существует")
                return
            category = Category.objects.create(name=new_category_name)
            # Новая категория по определению ещё без единой подкатегории —
            # значит и подкатегория обязана быть новой тоже (см. докстринг
            # модуля и dialog-new-summary в дизайн-макете), выбор
            # существующей подкатегории здесь не рассматривается вообще,
            # даже если subcategory_id пришёл в обход интерфейса.
            subcategory_name = new_subcategory_name or new_category_name
            subcategory = Subcategory.objects.create(name=subcategory_name)
            CategorySubcategory.objects.create(category=category, subcategory=subcategory)
        else:
            category = Category.objects.filter(id=category_id).first()
            if not category:
                messages.error(request, "Выберите категорию")
                return
            if new_subcategory_name:
                existing_sub = {
                    s.casefold()
                    for s in Subcategory.objects.filter(categories=category).values_list("name", flat=True)
                }
                if new_subcategory_name.casefold() in existing_sub:
                    messages.error(request, f"Подкатегория «{new_subcategory_name}» уже есть в этой категории")
                    return
                subcategory = Subcategory.objects.create(name=new_subcategory_name)
                CategorySubcategory.objects.create(category=category, subcategory=subcategory)
            else:
                subcategory = Subcategory.objects.filter(id=subcategory_id, categories=category).first()
                if not subcategory:
                    messages.error(request, "Выберите подкатегорию")
                    return

        skill = Skill.objects.filter(name__iexact=name).first()
        if skill:
            if skill.is_active:
                messages.error(request, f"Навык «{name}» уже есть в каталоге")
                return
            # Навык раньше был мягко удалён (is_active=False) — "добавление"
            # с тем же именем его просто возвращает в каталог, а не создаёт
            # дубль с тем же названием (unique нет на уровне БД у Skill.name,
            # но два навыка с одинаковым именем в одном каталоге не имели бы
            # смысла для человека, который их выбирает).
            skill.is_active = True
            skill.name = name
            skill.save(update_fields=["is_active", "name"])
        else:
            skill = Skill.objects.create(name=name, is_active=True)

        SubcategorySkill.objects.get_or_create(subcategory=subcategory, skill=skill)

    messages.success(request, f"Навык «{name}» добавлен в каталог")


def _handle_delete_skill(request):
    """Мягкое удаление — см. докстринг модуля, почему не .delete()."""
    skill_id = request.POST.get("skill_id")
    skill = Skill.objects.filter(id=skill_id, is_active=True).first()
    if not skill:
        messages.error(request, "Навык не найден")
        return
    skill.is_active = False
    skill.save(update_fields=["is_active"])
    messages.success(request, f"Навык «{skill.name}» удалён из каталога")


@login_required(login_url="/login/")
def analytics_page(request):
    if not _can_view(request.user):
        return redirect("my-profile")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_skill":
            _handle_add_skill(request)
        elif action == "delete_skill":
            _handle_delete_skill(request)
        else:
            messages.error(request, "Неизвестное действие")
        # Фильтр "Отдел" сохраняем через redirect с тем же query-параметром,
        # иначе после POST HR молча вернуло бы на "Все отделы" — тот же
        # принцип, что и next= в profile_page.py, только через querystring,
        # раз тут нет formы-обёртки с next-полем на КАЖДОЙ форме диалога.
        department_id = request.POST.get("department_id") or request.GET.get("department_id")
        if department_id:
            return redirect(f"/analytics/?department_id={department_id}")
        return redirect("analytics-page")

    department = None
    department_id = request.GET.get("department_id")
    if department_id:
        department = Department.objects.filter(id=department_id).first()

    # .values(...) вместо values_list("id", flat=True) — тем же запросом
    # сразу достаём поля для выпадающего списка "кто входит в выборку"
    # под пилюлей "Сотрудников" (см. an-members-dropdown в analytics.html):
    # раньше пилюля была просто числом, посмотреть ФИО можно было только
    # уйдя на другую страницу. member_ids ниже (для всех остальных
    # агрегатов) — по-прежнему просто список id, порядок/поля тут ни на что
    # не влияют.
    members_qs = _scope_users_qs(department).order_by("full_name").values(
        "id", "full_name", "position", "photo"
    )
    members = list(members_qs)
    member_ids = [m["id"] for m in members]

    top_skills, rare_skills = _top_and_rare_skills(member_ids)

    # Для каскада "Категория -> Подкатегория" в диалоге "Управление
    # навыками" (см. analytics.html): JS читает эту структуру целиком
    # (через json_script) и на изменение <select> категории перестраивает
    # список опций <select> подкатегории — тот же принцип каскада, что и
    # cascadeSubcategoryOptions() в reserve.html, но данные проще (не
    # плоский список с "|"-разделителем, тут ровно то дерево, что нужно).
    categories_data = [
        {
            "id": c.id,
            "name": c.name,
            "subcategories": [{"id": s.id, "name": s.name} for s in c.subcategories.all()],
        }
        for c in Category.objects.prefetch_related("subcategories").order_by("name")
    ]

    skills_total = Skill.objects.filter(is_active=True).count()

    context = {
        "departments": Department.objects.order_by("name"),
        "selected_department": department,
        "member_count": len(member_ids),
        "members": members,
        "skills_total": skills_total,
        "skills_total_label": _ru_plural(skills_total, "навык", "навыка", "навыков"),
        "confirmation_rate": _confirmation_rate(member_ids),
        "category_shares": _category_shares(),
        "top_skills": top_skills,
        "rare_skills": rare_skills,
        "level_distribution": _level_distribution(member_ids),
        "skill_gaps": _skills_with_gap(member_ids),
        "skills_catalog": _skills_catalog_for_dialog(),
        "categories_data": categories_data,
    }
    return render(request, "analytics.html", context)
