"""/reserve/ — HTML-страница «Кадровый резерв», БЕЗ DRF.

ДОБАВЛЕНИЕ СОТРУДНИКА (кнопка "Добавить сотрудника", POST action=
add_employee, см. _handle_add_employee): пока в проекте нет интеграции с
Yandex 360/Zulip (см. department_page.py — раньше там была похожая форма,
убранная именно по этой причине, "решение не принято"), но приложению
нужен хоть какой-то способ завести нового человека, иначе им просто
неоткуда взяться. Договорились сделать здесь МИНИМАЛЬНО достаточную форму:
ФИО/email/отдел/должность/роль/стажёр, пароль генерируется автоматически
(HR его не придумывает) и показывается ОДИН РАЗ сразу после создания — в
отдельном диалоге (не в обычной зелёной плашке сообщений, там пароль было
легко потерять/проскроллить), второй раз его нигде не видно, HR должен
сам передать его новому сотруднику лично. Учётка сразу is_active=True ("работающий" — см.
докстринг User.is_active в api/models.py, по умолчанию в модели False,
здесь это осознанно переопределяется).

Раньше страница была полностью server-side: каждый фильтр слался на
сервер новым GET-запросом (department/category/subcategory/skill/status/
level_min/level_max/only_interns/only_terminated/search/sort), из-за
чего при каждом клике перезагружалась вся страница — сначала это
пробовали лечить через AJAX-подгрузку (fetch того же URL без полной
навигации), но по итогу решили сделать так же, как в matrix_page.py/
matrix.html: сервер ОДИН РАЗ отдаёт вообще ВСЕХ сотрудников со всеми
данными, нужными для фильтрации, а дальше вся фильтрация — целиком на
JS (см. extra_js в reserve.html), без единого запроса к серверу вообще.

Из-за этого решения вся логика совмещения фильтров (категория/
подкатегория/навык через реальные M2M-связи Category->Subcategory->
Skill, диапазон уровня, статус подтверждения и т.д. — та самая, что
чинили из-за бага с несовместимыми фильтрами) теперь ПРОДУБЛИРОВАНА на
JS. Это осознанный компромисс: два места с одной и той же бизнес-
логикой придётся держать в синхроне вручную, если что-то в правилах
фильтрации изменится.

Списки подкатегорий/навыков с данными для каскада (data-categories/
data-subcategories) теперь строит api/helpers.py (build_subcategories_
cascade_data/build_skills_cascade_data) — та же самая функция, что
использует и matrix_page.py, чтобы в обоих местах карточка "категория ->
подкатегория -> навык" считалась ОДИНАКОВО, без дублирования в двух
view-файлах.

Доступ: только HR (см. _can_view) — остальных отправляем в их профиль,
тот же приём, что и в approvals_page.py.

УПРАВЛЕНИЕ ОТДЕЛАМИ (кнопка "Управление отделами" в шапке, POST action=
create_department/delete_department, см. _handle_create_department/
_handle_delete_department) и УДАЛЕНИЕ СОТРУДНИКА (корзина на карточке,
action=delete_employee, см. _handle_delete_employee) — из трёх вариантов
размещения, показанных пользователю макетами, выбран вариант с отдельным
диалогом управления отделами (не смешивает "выбрать отдел для фильтра" и
"выбрать отдел для удаления" в одном и том же <select>). Оба удаления идут
через общий #confirmDialog из base.html (data-confirm-message на форме) —
подтверждение обязательно, отдельного JS под это здесь нет.

РЕДАКТИРОВАНИЕ ПРОФИЛЯ ("Редактировать профиль" на карточке) — раньше
диалог здесь редактировал только phone/city/about/photo, хотя на самой
странице профиля (profile.html) HR уже мог менять ФИО/email/должность/
отдел у ЧУЖОГО профиля (см. hr_editing_other в profile_page.py — это
было сделано первым шагом, "Кадровый резерв" явно оставили на потом).
Теперь тот же расширенный набор полей перенесён и сюда — диалог в
reserve.html как отправлял, так и отправляет форму напрямую на
profile_page() (action=update_profile, next=reserve-page), никакой новой
серверной логики в этом файле для этого не появилось: _build_employees()
только добавил email/department_id в данные карточки (см. ниже), чтобы
было чем предзаполнить новые поля диалога — вся валидация/сохранение
по-прежнему в _handle_update_profile (profile_page.py).

ВАЖНО: HR может открыть этот же диалог и для СВОЕЙ СОБСТВЕННОЙ карточки
(см. docstring _handle_delete_employee ниже — HR тоже есть в списке).
В этом случае hr_editing_other на бэкенде будет False (request.user.id
== user.id), и _handle_update_profile молча проигнорирует ФИО/email/
должность/отдел, сохранив только phone/city/about — как и раньше. Чтобы
это не выглядело как "поля есть, а изменения теряются", JS в reserve.html
(см. extra_js) показывает расширенные поля ТОЛЬКО когда открыта карточка
ДРУГОГО сотрудника — сравнивает data-user-id кнопки с id текущего
залогиненного HR (передан в шаблон как CURRENT_USER_ID). На своей же
карточке диалог выглядит как раньше — только телефон/город/"о себе"
(фото в этом диалоге не было и не появилось — этого не просили и на
странице профиля фото HR тоже не может менять чужое).
"""
import secrets
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from api.helpers import build_skills_cascade_data, build_subcategories_cascade_data
from api.models import Category, Department, Role, User, UserRole
from .profile_page import VALID_LEVELS

MIN_LEVEL = min(VALID_LEVELS)
MAX_LEVEL = max(VALID_LEVELS)

# Без похожих на вид символов (0/O, 1/l/I) — HR будет читать и передавать
# этот пароль человеку "на словах"/в переписке, важно не путать символы.
_PASSWORD_ALPHABET = "".join(
    c for c in (string.ascii_letters + string.digits) if c not in "0O1lI"
)
_PASSWORD_LENGTH = 10


def _generate_password() -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(_PASSWORD_LENGTH))


def _handle_add_employee(request):
    full_name = (request.POST.get("full_name") or "").strip()
    email = (request.POST.get("email") or "").strip().lower()
    position = (request.POST.get("position") or "").strip()
    department_id = request.POST.get("department_id") or None
    role_id = request.POST.get("role_id") or None
    is_intern = request.POST.get("is_intern") == "on"

    if not full_name:
        messages.error(request, "ФИО обязательно")
        return
    if not email:
        messages.error(request, "Email обязателен")
        return
    if User.objects.filter(email=email).exists():
        messages.error(request, f"Пользователь с email {email} уже существует")
        return

    role = Role.objects.filter(id=role_id).first() if role_id else None
    if not role:
        messages.error(request, "Нужно выбрать роль")
        return

    department = Department.objects.filter(id=department_id).first() if department_id else None

    generated_password = _generate_password()
    user = User.objects.create_user(
        email=email,
        password=generated_password,
        full_name=full_name,
        position=position or None,
        department=department,
        is_intern=is_intern,
        # См. докстринг модуля — по умолчанию в модели is_active=False,
        # здесь осознанно True: только что добавленный человек это
        # "работающий" сотрудник, а не "уволен".
        is_active=True,
    )
    UserRole.objects.create(user=user, role=role)

    messages.success(request, f"Сотрудник «{full_name}» добавлен.")
    # Пароль — ОТДЕЛЬНЫМ сообщением с особым extra_tags, а не текстом внутри
    # обычной зелёной плашки выше. Раньше пароль был просто частью текста
    # в самом верху страницы — легко потерять/случайно проскроллить мимо,
    # особенно если карточек много. Теперь reserve.html находит именно это
    # сообщение по extra_tags (см. message.tags) и вместо плашки открывает
    # отдельный диалог с крупным моноширинным паролем + кнопкой "Скопировать"
    # (см. extra_js в reserve.html) — то же самое "показываем один раз",
    # просто заметнее и сложнее случайно пропустить.
    messages.success(request, generated_password, extra_tags="resv-password-flash")


def _handle_create_department(request):
    """POST-обработчик формы добавления отдела в диалоге "Управление
    отделами" (см. #manageDepartmentsDialog в reserve.html).

    У Department.name нет unique=True на уровне БД (см. api/models.py) —
    проверяем уникальность сами (без учёта регистра), иначе в фильтре
    "Отдел" на этой же странице появились бы два визуально одинаковых
    пункта, и было бы не понять, какой из них выбирать.

    Сравниваем через Python str.casefold(), а НЕ через ORM-lookup
    name__iexact — на SQLite (см. settings_sqlite_test.py, использовался
    при локальном тестировании) __iexact транслируется в LIKE, а встроенный
    LIKE в SQLite регистронезависим только для ASCII-символов, кириллицу
    не сворачивает вообще (без подключения расширения ICU) — "Отдел" и
    "отдел" там считались бы РАЗНЫМИ строками, дубликат проходил бы молча.
    В проде (settings.py — PostgreSQL) name__iexact сработал бы верно, но
    полагаться на разное поведение разных БД для одной и той же проверки
    не стоит — casefold() в Python корректно сворачивает регистр у любого
    алфавита независимо от backend'а БД под капотом.
    """
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "Название отдела обязательно")
        return

    max_name_length = Department._meta.get_field("name").max_length
    if len(name) > max_name_length:
        messages.error(request, f"Название отдела не должно превышать {max_name_length} символов")
        return

    existing_names_casefolded = {n.casefold() for n in Department.objects.values_list("name", flat=True)}
    if name.casefold() in existing_names_casefolded:
        messages.error(request, f"Отдел «{name}» уже существует")
        return

    Department.objects.create(name=name)
    messages.success(request, f"Отдел «{name}» добавлен")


def _handle_delete_department(request):
    """POST-обработчик кнопки-корзины у строки отдела в том же диалоге.

    У User.department стоит on_delete=SET_NULL (см. api/models.py) — при
    удалении отдела сотрудники НЕ удаляются и НЕ блокируют удаление, они
    просто становятся "без отдела" (то же значение, что и у сотрудника,
    которому отдел вообще не назначали). Подтверждение перед отправкой —
    через общий #confirmDialog (data-confirm-message на форме в
    reserve.html), само удаление тут уже безусловное.
    """
    department_id = request.POST.get("department_id")
    department = Department.objects.filter(id=department_id).first()
    if not department:
        messages.error(request, "Отдел не найден")
        return

    name = department.name
    employee_count = department.users.count()
    department.delete()

    if employee_count:
        messages.success(
            request,
            f"Отдел «{name}» удалён. Без отдела остались: {employee_count}.",
        )
    else:
        messages.success(request, f"Отдел «{name}» удалён")


def _handle_delete_employee(request):
    """POST-обработчик кнопки-корзины на карточке сотрудника.

    Список карточек (_build_employees) строится по ВСЕМ User.objects.all()
    без исключения текущего HR — значит и собственная карточка HR тоже
    попадает в список с этой же кнопкой. Явно запрещаем удалить самого
    себя: сервер всё равно отклонит запрос, но кнопка-корзина на своей же
    карточке скрыта и в самом шаблоне (см. reserve.html, employee.id ==
    request.user.id) — эта проверка здесь на случай прямого POST в обход
    разметки, а не единственная линия защиты.

    Каскады при User.delete() (см. api/models.py): UserRole/UserSkill/
    UserProject.user/UserComment — все CASCADE, удаляются вместе с
    пользователем. Project.created_by — SET_NULL, созданные им проекты
    остаются, просто без владельца. RESTRICT нигде на User не завязан,
    так что удаление не может неожиданно упасть с ошибкой БД.
    """
    user_id = request.POST.get("user_id")
    if str(user_id) == str(request.user.id):
        messages.error(request, "Нельзя удалить самого себя")
        return

    employee = User.objects.filter(id=user_id).first()
    if not employee:
        messages.error(request, "Сотрудник не найден")
        return

    name = employee.full_name
    employee.delete()
    messages.success(request, f"Сотрудник «{name}» удалён")


def _can_view(user) -> bool:
    return user.has_role("HR")


def _build_employees():
    users_qs = (
        User.objects.select_related("department")
        .prefetch_related("user_skills__skill__subcategories__categories")
        .order_by("full_name")
    )

    employees = []
    for user in users_qs:
        skills = []
        for user_skill in user.user_skills.all():
            skill = user_skill.skill
            subcategory_names = sorted(s.name for s in skill.subcategories.all())
            category_names = sorted({
                c.name for s in skill.subcategories.all() for c in s.categories.all()
            })
            skills.append({
                "skill": skill.name,
                "level": user_skill.level,
                "approved": user_skill.is_approved,
                "subcategories": subcategory_names,
                "categories": category_names,
            })

        employees.append({
            "id": user.id,
            "full_name": user.full_name,
            "position": user.position or "",
            # phone/city/about/email/department_id — только чтобы
            # предзаполнить диалог "Редактировать профиль" (см.
            # reserve.html/extra_js) текущими значениями, когда HR
            # открывает его с этой карточки. Сама отправка формы идёт на
            # уже существующий profile_page.py (action=update_profile) —
            # здесь новой логики сохранения нет, только показ того, что
            # уже есть. email/department_id добавлены вместе с переносом
            # расширенного HR-редактирования сюда же (см. docstring модуля
            # выше и profile_page.py/_handle_update_profile) — раньше
            # диалог редактировал только phone/city/about/photo.
            "phone": user.phone or "",
            "city": user.city or "",
            "about": user.about or "",
            "email": user.email,
            "department_id": user.department_id,
            "photo": user.photo,
            "is_intern": user.is_intern,
            "is_active": user.is_active,
            "department": user.department.name if user.department_id else "",
            # Целое число, не float — Django рендерит float с запятой как
            # разделитель дробной части (локаль), и JS Number("...,...")
            # в data-атрибуте молча даёт NaN, из-за чего сортировка
            # "Последние добавленные" переставала работать без единой
            # ошибки в консоли.
            "created_ts": int(user.created_at.timestamp()) if user.created_at else 0,
            "skills": skills,
            # id для {% json_script %} в шаблоне — там же, где карточка,
            # лежит <script type="application/json"> с этим списком навыков,
            # JS читает его по id при фильтрации/сравнении с фильтрами.
            "skills_json_id": f"skills-data-{user.id}",
        })
    return employees


@login_required(login_url="/login/")
def reserve_page(request):
    if not _can_view(request.user):
        return redirect("my-profile")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_employee":
            _handle_add_employee(request)
        elif action == "create_department":
            _handle_create_department(request)
        elif action == "delete_department":
            _handle_delete_department(request)
        elif action == "delete_employee":
            _handle_delete_employee(request)
        else:
            messages.error(request, "Неизвестное действие")
        return redirect("reserve-page")

    context = {
        "employees": _build_employees(),
        "min_level": MIN_LEVEL,
        "max_level": MAX_LEVEL,
        # Все уровни между MIN_LEVEL и MAX_LEVEL — для подписей "1 2 3 4"
        # под слайдером диапазона уровня (раньше подписывались только
        # края диапазона, средние уровни были не подписаны).
        "levels": list(range(MIN_LEVEL, MAX_LEVEL + 1)),
        "departments": Department.objects.order_by("name"),
        "categories": Category.objects.order_by("name"),
        "subcategories": build_subcategories_cascade_data(),
        "skills": build_skills_cascade_data(),
        # Для селекта "Роль" в диалоге "Добавить сотрудника" — см.
        # _handle_add_employee. Порядок ролей осознанно фиксированный
        # (Employee первым, как самый частый выбор для нового человека),
        # а не просто order_by("name") — HR/Manager видно, но реже нужны.
        "roles": sorted(
            Role.objects.all(),
            key=lambda r: {"Employee": 0, "Manager": 1, "HR": 2}.get(r.name, 99),
        ),
    }
    return render(request, "reserve.html", context)
