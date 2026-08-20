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
            # phone/city/about — только чтобы предзаполнить диалог
            # "Редактировать профиль" (см. reserve.html/extra_js) текущими
            # значениями, когда HR открывает его с этой карточки. Сама
            # отправка формы идёт на уже существующий profile_page.py
            # (action=update_profile) — здесь новой логики сохранения нет,
            # только показ того, что уже есть.
            "phone": user.phone or "",
            "city": user.city or "",
            "about": user.about or "",
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
        if request.POST.get("action") == "add_employee":
            _handle_add_employee(request)
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
