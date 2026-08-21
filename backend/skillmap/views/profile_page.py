"""/profile/<user_id>/ — HTML-страница профиля, БЕЗ DRF.

Отдельный путь, отдельный рендер, без визуальной составляющей — фронт
оформит позже. Выводит из БД только те данные, что нужны для профиля.

Функционал (всё через обычный POST + ORM, без DRF):
- Редактирование phone/city/about — доступно самому юзеру (свой профиль),
  HR (любой профиль) и Manager (профиль сотрудника СВОЕГО отдела, см.
  _can_edit) через один и тот же диалог/action=update_profile.

  РЕДАКТИРОВАНИЕ ЧУЖОГО ПРОФИЛЯ ЦЕЛИКОМ (HR): по запросу — раньше
  фраза "Должность (position) НЕ редактируется самим юзером — её меняют
  HR/Manager отдельно (тут не реализовано)" тут и стояла как заготовка на
  будущее. Теперь реализовано, но ТОЛЬКО для HR и ТОЛЬКО когда HR смотрит
  ЧУЖОЙ профиль (не свой собственный) — см. hr_editing_other в
  profile_page()/_handle_update_profile. В этом режиме дополнительно можно
  менять ФИО/email/должность/отдел, а ФОТО — намеренно НЕЛЬЗЯ (по прямому
  запросу пользователя: "любую информацию, кроме фото") — file input
  фотографии в этом варианте диалога (см. profile/_edit_dialog.html)
  просто отсутствует в разметке, а _handle_update_profile ниже в этой
  ветке вообще не трогает request.FILES. Self-edit (свой профиль) и
  Manager-edit (сотрудник своего отдела) НЕ затронуты этим изменением —
  у них по-прежнему только phone/city/about/photo, как было раньше; сам
  UI-доступ (кнопка-карандаш) для Manager, редактирующего чужой профиль,
  по-прежнему нигде не показан (см. profile.html) — это уже существовавшее
  до этой правки положение дел, отдельно не трогали.

  Кадровый резерв (reserve.html) со своим отдельным диалогом
  редактирования (тоже action=update_profile, тоже HR) пока НЕ
  переведён на расширенный набор полей — это следующий шаг отдельным
  запросом (см. docstring reserve_page.py), там пока прежний набор
  (phone/city/about/photo).
- Загрузка фото как реального файла (request.FILES). В БД поле photo —
  TEXT, туда пишется только путь/URL к сохранённому файлу.
- Резюме — тоже реальный файл (TEXT-поле resume), но грузить и видеть
  его может ТОЛЬКО HR (см. can_manage_resume/_handle_update_resume/
  _handle_delete_resume) — обычный сотрудник (даже свой собственный
  профиль) и Manager резюме не видят и не грузят вовсе.
- Навыки: добавление нового (выбор из списка + уровень), изменение
  уровня существующей ЗАЯВКИ, удаление (заявки ИЛИ уже подтверждённой
  строки — на удаление это ограничение не распространяется).

  У одного навыка может быть до двух строк UserSkill одновременно:
  подтверждённая (is_approved=True) и заявка на рассмотрении
  (is_approved=False) — см. docstring модели UserSkill в api/models.py.
  Добавление нового уровня НЕ трогает уже подтверждённый уровень: та
  строка живёт своей жизнью, пока HR/Manager не подтвердит новую заявку
  (см. approvals_page.py — там же старый подтверждённый уровень удаляется).
  Редактировать (менять уровень) можно только заявку, не подтверждённую
  строку — иначе пришлось бы либо тайно обходить подтверждение, либо
  заводить третью строку на один навык, а инвариант — максимум две.

  РЕДАКТИРОВАНИЕ ЧУЖИХ НАВЫКОВ (HR): по запросу — раньше add_skill/
  update_skill/delete_skill были доступны только через UI своего же
  профиля (request.user == profile_user), хотя серверная проверка прав
  (_can_edit) и так уже разрешала HR/Manager нужные действия — просто
  кнопок было неоткуда нажать на чужом профиле. Теперь при hr_editing_other
  (HR смотрит ЧУЖОЙ профиль — см. profile_page()) в разметке (profile.html/
  _skill_dialog.html) показывается та же самая секция "Навыки", что и
  на своём профиле — то же самое действие, что сотрудник мог бы сделать
  сам себе: add_skill/update_skill по-прежнему создают/меняют ЗАЯВКУ
  (is_approved=False), которую всё так же отдельно подтверждает Manager
  отдела на "Подтверждении навыков" (см. approvals_page.py) — HR никого
  не подтверждает напрямую в обход этого процесса, никакого нового
  "прямого подтверждения" тут не появилось. delete_skill удаляет любую
  строку (заявку или уже подтверждённую), как и при самостоятельном
  удалении. Сами обработчики (_handle_add_skill/_handle_update_skill/
  _handle_delete_skill) не менялись — им всё равно, кто именно (сам
  сотрудник или HR) прислал action, права проверяются один раз на входе
  в profile_page() через _can_edit; в текстах ошибок про "уже
  подтверждённый уровень" теперь просто различается "у вас"/"у {имя}" в
  зависимости от того, свой это профиль или чужой (иначе сообщение
  "у вас уже подтверждён..." было бы неверным, когда действие выполняет
  HR за другого).

  Manager, редактирующий сотрудника своего отдела — как и с профилем выше
  (см. РЕДАКТИРОВАНИЕ ЧУЖОГО ПРОФИЛЯ ЦЕЛИКОМ) — UI-кнопок в разделе
  "Навыки" по-прежнему не видит; серверная проверка (_can_edit) для него
  не менялась (не сужена и не расширена), это не входило в запрос.

  Кадровый резерв (reserve.html) — эта возможность туда не переносилась,
  там свой собственный набор действий (см. docstring reserve_page.py),
  навыков там нет вовсе.
- Комментарии (UserComment) — заметки HR/руководителя о сотруднике c
  оценкой 1-3 (см. COMMENT_LEVEL_LABELS). Виден и доступен для добавления
  список только HR (про любого сотрудника) и Manager (только про
  сотрудников своего отдела) — см. _can_manage_comments. Сам сотрудник
  комментарии о себе не видит НИКОГДА, даже если у него есть роль
  HR/Manager и он смотрит свой профиль. Редактировать/удалять может
  только автор конкретного комментария.

Все POST-запросы этой страницы различаются полем action в форме:
  update_profile / update_resume / delete_resume / add_skill /
  update_skill / delete_skill / add_comment / update_comment /
  delete_comment
"""
import uuid
from random import randint

from PIL import Image, UnidentifiedImageError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from api.models import Department, Skill, User, UserComment, UserProject, UserSkill

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
# Резюме раньше грузилось вообще без проверки размера (в отличие от фото
# чуть выше) — HR мог залить произвольно большой файл, ничем не
# ограниченный диск копил бы мусор (аудит, п. 4.1). PDF/DOCX обычно
# заметно тяжелее фото, поэтому лимит выше, а не тот же самый.
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_PHOTO_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_RESUME_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}

# ФИКС по итогам аудита (пункты 1.5/1.6): раньше файл сохранялся под
# ИСХОДНЫМ именем (uploaded_file.name как есть), а его "тип" проверялся
# только по Content-Type из формы — заголовку, который полностью
# контролирует отправитель и который никак не привязан к реальному
# содержимому файла. Раздача /media/ при этом шла через
# django.views.static.serve, который определяет Content-Type ОТДАВАЕМОГО
# ответа по РАСШИРЕНИЮ файла. Итог: загрузив файл "фото.svg" с
# содержимым <script>...</script>, но с Content-Type: image/png в форме,
# можно было пройти проверку — а при отдаче браузер получал его как
# image/svg+xml и исполнял скрипт (см. serve_photo/serve_resume в
# media_views.py — теперь ещё и раздача авторизована, это отдельный фикс
# пункта 1.5, но проверка ниже нужна в любом случае — она не про то, кто
# видит файл, а про то, что вообще лежит на диске).
#
# Теперь: (1) расширение на диске выбирается ТОЛЬКО по реально
# распознанному формату содержимого (Pillow для фото — честное
# декодирование заголовка, не по имени/Content-Type; сигнатура первых
# байт для резюме — PDF/DOCX), никогда не по имени файла из формы; (2)
# само имя файла на диске — случайное (uuid4), а не то, что прислал
# браузer — предсказуемые имена также позволяли просто угадать/перебрать
# чужой файл по прямой ссылке (пункт 1.5).
_PHOTO_FORMAT_EXTENSIONS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}


def _detect_photo_extension(uploaded_file):
    """'jpg'/'png'/'webp', если файл — ДЕЙСТВИТЕЛЬНО валидное изображение
    одного из этих форматов (проверяем декодированием через Pillow),
    иначе None. uploaded_file.seek(0) в конце — обязательно, иначе
    default_storage.save() ниже получит файл с "докрученной до конца"
    позицией чтения и сохранит 0 байт."""
    try:
        img = Image.open(uploaded_file)
        img.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        # SyntaxError — отдельно от UnidentifiedImageError/OSError/ValueError:
        # Pillow кидает именно его (а не один из уже перечисленных типов) на
        # некоторых видах повреждённых файлов — например PNG с несовпадающей
        # CRC-суммой у чанка IDAT. Раньше это не ловилось здесь и падало
        # необработанным исключением прямо в 500-ку на всю страницу профиля,
        # хотя весь смысл этой функции — вернуть None на "файл не похож на
        # настоящее изображение", а не уронить запрос. Задевало не только
        # специально подделанный вредоносный файл, но и обычного
        # пользователя с чуть битым PNG (нашли ровно так — тестовым файлом,
        # без всякого злого умысла).
        return None
    finally:
        uploaded_file.seek(0)

    # После verify() PIL требует переоткрыть файл заново, чтобы читать
    # что-либо ещё (сам verify() — одноразовая проверка целостности) —
    # тот же файл-объект, просто заново, курсор уже сброшен в finally выше.
    try:
        img = Image.open(uploaded_file)
        fmt = img.format
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return None
    finally:
        uploaded_file.seek(0)

    return _PHOTO_FORMAT_EXTENSIONS.get(fmt)


_RESUME_SIGNATURES = {
    b"%PDF-": "pdf",
    b"PK\x03\x04": "docx",  # .docx — это ZIP-архив, сигнатура обычного zip-файла
}


def _detect_resume_extension(uploaded_file):
    """'pdf'/'docx' по первым байтам файла (реальной сигнатуре формата),
    не по Content-Type/имени из формы — та же причина, что и у фото
    выше. Полную внутреннюю структуру .docx не разбираем (это избыточно
    для внутреннего HR-инструмента) — сигнатуры ZIP достаточно, чтобы
    отсечь произвольный файл с подделанным Content-Type."""
    header = uploaded_file.read(8)
    uploaded_file.seek(0)
    for signature, ext in _RESUME_SIGNATURES.items():
        if header.startswith(signature):
            return ext
    return None

PROFILE_LEVEL_LABELS = {1: "Новичок", 2: "Опытный", 3: "Продвинутый", 4: "Эксперт"}
PROFILE_LEVEL_LABELS_EN = {1: "novice", 2: "experienced", 3: "advanced", 4: "expert"}
VALID_LEVELS = {1, 2, 3, 4}

# UserComment.level — оценка сотрудника автором комментария (1-3), см.
# docstring модуля выше и _can_manage_comments.
COMMENT_LEVEL_LABELS = {1: "Низкая", 2: "Средняя", 3: "Высокая"}
COMMENT_LEVEL_CLASS = {1: "low", 2: "medium", 3: "high"}


def _save_uploaded_file(uploaded_file, subdir: str, extension: str) -> str:
    """Сохраняет файл на диск (MEDIA_ROOT/subdir/...) под случайным именем
    (uuid4 + РЕАЛЬНО распознанное расширение, см. _detect_photo_extension/
    _detect_resume_extension выше) и возвращает URL для записи в БД
    (TEXT). Имя из uploaded_file.name больше нигде не используется — ни
    для расширения, ни как часть имени на диске (см. комментарий у
    _PHOTO_FORMAT_EXTENSIONS выше, пункты 1.5/1.6 аудита)."""
    filename = f"{uuid.uuid4().hex}.{extension}"
    path = default_storage.save(f"{subdir}/{filename}", uploaded_file)
    return default_storage.url(path)


def _delete_uploaded_file(url: str | None) -> None:
    """Удаляет с диска файл, на который раньше указывало сохранённое в БД
    значение photo/resume (URL, полученный из _save_uploaded_file выше).

    Раньше ни замена, ни удаление фото/резюме не трогали старый файл на
    диске вообще — просто перезаписывался путь в БД, а прежний файл
    оставался лежать в MEDIA_ROOT бессрочно, ничем не связанный ни с одной
    записью (аудит, п. 4.2). Молча ничего не делает, если url пуст, не
    похож на файл этого же storage, или файл уже отсутствует — вызывается
    и там, где старого файла могло не быть вовсе (первая загрузка).

    Storage хранит файлы по ПУТИ относительно MEDIA_ROOT ("photos/xxx.jpg"),
    а в БД лежит URL ("/media/photos/xxx.jpg", см. default_storage.url()
    в _save_uploaded_file) — префикс отрезаем через default_storage.url("")
    (тот же самый MEDIA_URL, каким бы он ни был настроен), а не хардкодом
    "/media/", чтобы не разъехаться при смене конфигурации storage."""
    if not url:
        return

    base_url = default_storage.url("")
    if not url.startswith(base_url):
        return

    relative_path = url[len(base_url):]
    if not relative_path:
        return

    try:
        if default_storage.exists(relative_path):
            default_storage.delete(relative_path)
    except OSError:
        # Гонка/права на файловой системе — не должны валить сохранение
        # нового файла (это чисто уборка за старым), просто оставляем
        # старый файл-сирота на диске, как было и раньше до этого фикса.
        pass


def _skill_display_name(skill) -> str:
    """'{подкатегория} ({скилл})', либо просто имя скилла, если подкатегории нет.

    Раньше — skill.subcategories.first(). У Subcategory нет Meta.ordering,
    поэтому .first() молча добавляет свой order_by('pk') — новый queryset,
    который не берётся из кеша prefetch_related("skill__subcategories")/
    ("subcategories") (см. вызовы ниже) — вместо переиспользования уже
    загруженных данных на каждый вызов идёт отдельный SQL-запрос (аудит,
    п. 3.4, тот же паттерн, что и в User.primary_role в api/models.py).
    list(skill.subcategories.all()) корректно попадает в prefetch-кеш."""
    subcategories = list(skill.subcategories.all())
    if subcategories:
        return f"{subcategories[0].name} ({skill.name})"
    return skill.name


def _parse_level(raw_value):
    """Возвращает int уровня (1-4) или None, если значение некорректно."""
    try:
        level = int(raw_value)
    except (TypeError, ValueError):
        return None
    return level if level in VALID_LEVELS else None


def _handle_update_profile(request, user):
    """См. docstring модуля — раздел "РЕДАКТИРОВАНИЕ ЧУЖОГО ПРОФИЛЯ ЦЕЛИКОМ".

    hr_editing_other: HR смотрит НЕ свой профиль. Только в этом режиме
    форма (см. profile/_edit_dialog.html) присылает ещё и full_name/email/
    position/department_id — во всех остальных случаях (свой профиль,
    Manager редактирует сотрудника своего отдела, HR редактирует СВОЙ
    профиль) этих полей в POST просто нет, request.POST.get(...) для них
    ничего не пришлёт, поэтому ветка ниже физически не может что-то
    затронуть, даже если вдруг окажется достижима — но для ясности и на
    случай прямого POST в обход разметки всё равно явно ограничена этим
    флагом, а не просто "есть ли full_name в POST".
    """
    hr_editing_other = request.user.has_role("HR") and request.user.id != user.id

    user.phone = (request.POST.get("phone") or "").strip()
    user.city = (request.POST.get("city") or "").strip()
    user.about = (request.POST.get("about") or "").strip()
    update_fields = ["phone", "city", "about"]

    if hr_editing_other:
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        position = (request.POST.get("position") or "").strip()
        department_id = request.POST.get("department_id") or None

        if not full_name:
            messages.error(request, "ФИО не может быть пустым")
            return
        max_name_length = User._meta.get_field("full_name").max_length
        if len(full_name) > max_name_length:
            messages.error(request, f"ФИО не должно превышать {max_name_length} символов")
            return

        if not email:
            messages.error(request, "Email не может быть пустым")
            return
        max_email_length = User._meta.get_field("email").max_length
        if len(email) > max_email_length:
            messages.error(request, f"Email не должен превышать {max_email_length} символов")
            return
        # exclude(id=user.id) — иначе сохранение БЕЗ изменения email того
        # же самого пользователя всегда ловило бы "уже используется" само
        # на себя (unique=True на User.email, см. api/models.py).
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, f"Email {email} уже используется другим пользователем")
            return

        max_position_length = User._meta.get_field("position").max_length
        if len(position) > max_position_length:
            messages.error(request, f"Должность не должна превышать {max_position_length} символов")
            return

        department = None
        if department_id:
            department = Department.objects.filter(id=department_id).first()
            if not department:
                messages.error(request, "Выбранный отдел не найден")
                return

        user.full_name = full_name
        user.email = email
        user.position = position or None
        user.department = department
        update_fields += ["full_name", "email", "position", "department"]
    else:
        # Фото — ТОЛЬКО в этой ветке (свой профиль или Manager редактирует
        # сотрудника своего отдела). Когда HR редактирует чужой профиль,
        # request.FILES вообще не смотрим — по прямому запросу пользователя
        # ("любую информацию, кроме фото") это единственное поле, которое
        # HR в чужом профиле поменять не может ни при каких условиях, даже
        # если бы файл каким-то образом оказался в запросе.
        photo = request.FILES.get("photo")
        if photo:
            if photo.content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
                messages.error(request, "Фото: разрешены только JPEG, PNG или WEBP")
            elif photo.size > MAX_PHOTO_SIZE:
                messages.error(request, "Фото: размер не должен превышать 5MB")
            else:
                # Content-Type в форме уже проверен выше, но это ЗАГОЛОВОК,
                # который отправитель полностью контролирует — отдельно,
                # независимо проверяем, что внутри файла ДЕЙСТВИТЕЛЬНО лежит
                # то самое изображение (см. _detect_photo_extension выше).
                extension = _detect_photo_extension(photo)
                if not extension:
                    messages.error(request, "Фото: файл повреждён или не является настоящим изображением")
                else:
                    # Старое фото на диске больше никому не нужно после
                    # замены — запоминаем его URL ДО перезаписи поля, чтобы
                    # удалить после успешного сохранения нового (аудит, п. 4.2).
                    old_photo_url = user.photo
                    user.photo = _save_uploaded_file(photo, "photos", extension)
                    _delete_uploaded_file(old_photo_url)
                    update_fields.append("photo")

    user.save(update_fields=update_fields)
    messages.success(request, "Профиль обновлён")


def _handle_update_resume(request, user):
    """Загрузка/замена резюме — только HR (см. docstring модуля).

    Резюме больше не часть общей формы update_profile — раньше сотрудник
    мог загрузить резюме себе сам через тот же диалог, что и телефон/фото,
    теперь это отдельное действие, доступное только автору с ролью HR
    (независимо от того, свой это профиль или чужой).
    """
    if not request.user.has_role("HR"):
        messages.error(request, "Загружать резюме может только HR")
        return

    resume = request.FILES.get("resume")
    if not resume:
        messages.error(request, "Файл резюме не выбран")
        return
    if resume.content_type not in ALLOWED_RESUME_CONTENT_TYPES:
        messages.error(request, "Резюме: разрешены только PDF или DOCX")
        return
    if resume.size > MAX_RESUME_SIZE:
        # Раньше проверки размера не было вообще — в отличие от фото чуть
        # выше (аудит, п. 4.1): HR мог залить произвольно большой файл,
        # ничем не ограниченный диск копил бы мусор.
        messages.error(request, "Резюме: размер не должен превышать 10MB")
        return

    # Content-Type из формы проверен выше, но это заголовок, который
    # отправитель полностью контролирует — отдельно проверяем реальные
    # байты файла (см. _detect_resume_extension выше).
    extension = _detect_resume_extension(resume)
    if not extension:
        messages.error(request, "Резюме: файл повреждён или не является настоящим PDF/DOCX")
        return

    # Старое резюме на диске больше никому не нужно после замены —
    # запоминаем его URL ДО перезаписи поля, удаляем после успешного
    # сохранения нового (аудит, п. 4.2, тот же приём, что и у фото выше).
    old_resume_url = user.resume
    user.resume = _save_uploaded_file(resume, "resumes", extension)
    user.save(update_fields=["resume"])
    _delete_uploaded_file(old_resume_url)
    messages.success(request, "Резюме обновлено")


def _handle_delete_resume(request, user):
    if not request.user.has_role("HR"):
        messages.error(request, "Удалять резюме может только HR")
        return

    # Раньше файл на диске не удалялся вообще — очищалось только поле в
    # БД, сам файл оставался лежать в MEDIA_ROOT бессрочно (аудит, п. 4.2).
    old_resume_url = user.resume
    user.resume = None
    user.save(update_fields=["resume"])
    _delete_uploaded_file(old_resume_url)
    messages.success(request, "Резюме удалено")


def _approved_level(user, skill):
    """Уровень уже ПОДТВЕРЖДЁННОЙ строки (user, skill), либо None, если её нет.

    Используется, чтобы не дать создать/сохранить заявку (is_approved=False)
    на уровень не выше уже подтверждённого — такая заявка бессмысленна
    (просить подтвердить то, что не выше уже подтверждённого, незачем), и
    инвариант в этом проекте: строка «заявка» существует, только пока
    approved_level < pending_level (см. docstring UserSkill и комментарий
    в _handle_add_skill/_handle_update_skill ниже).
    """
    row = UserSkill.objects.filter(user=user, skill=skill, is_approved=True).only("level").first()
    return row.level if row else None


def _handle_add_skill(request, user):
    """Добавляет новую заявку на навык (is_approved=False).

    Разрешено, даже если у пользователя уже есть ПОДТВЕРЖДЁННЫЙ уровень
    этого навыка — так и запрашивается повышение (например, был Docker 2
    подтверждён, отдельной заявкой просим Docker 4), но ТОЛЬКО если новый
    уровень строго выше уже подтверждённого — иначе заявка не имеет
    смысла (см. _approved_level) и не создаётся вовсе. Также не разрешено,
    если по этому навыку уже есть заявка на рассмотрении — второй
    одновременно быть не может, инвариант «максимум 2 строки на навык»
    (см. UserSkill).
    """
    skill_id = request.POST.get("skill_id")
    level = _parse_level(request.POST.get("level"))
    skill = Skill.objects.filter(id=skill_id, is_active=True).first()

    if not skill:
        messages.error(request, "Выбранный навык не найден")
        return
    if level is None:
        messages.error(request, "Уровень должен быть от 1 до 4")
        return

    if UserSkill.objects.filter(user=user, skill=skill, is_approved=False).exists():
        messages.error(request, f"По навыку «{skill.name}» уже есть заявка на рассмотрении")
        return

    approved_level = _approved_level(user, skill)
    if approved_level is not None and level <= approved_level:
        # "У вас"/"У {full_name}" — HR теперь может выполнять это же
        # действие за ДРУГОГО сотрудника (см. hr_editing_other в
        # profile_page()/шаблоне), и текст "у вас уже подтверждён" был бы
        # просто неверным (это не про самого HR), когда user != request.user.
        who = "у вас" if user.id == request.user.id else f"у «{user.full_name}»"
        messages.error(
            request,
            f"Уже подтверждён навык «{skill.name}» {who} на уровне "
            f"{PROFILE_LEVEL_LABELS[approved_level]} — заявка имеет смысл только на более высокий уровень",
        )
        return

    # Между .exists() чуть выше и .create() здесь есть окно для гонки —
    # двойной клик или два открытых окна успевают оба пройти проверку
    # .exists() до того, как первый .create() зафиксируется, и второй
    # .create() падает в необработанный IntegrityError (реальный инвариант
    # держится на unique_together(user, skill, is_approved) в БД, см.
    # UserSkill) — раньше это была голая 500-ка вместо опрятного сообщения
    # (аудит, п. 4.3).
    try:
        UserSkill.objects.create(
            user=user, skill=skill, level=level, is_approved=False, created_at=timezone.now()
        )
    except IntegrityError:
        messages.error(request, f"По навыку «{skill.name}» уже есть заявка на рассмотрении")
        return
    messages.success(request, f"Навык «{skill.name}» добавлен и отправлен на подтверждение")


def _handle_update_skill(request, user):
    """Меняет уровень в заявке (is_approved=False).

    Подтверждённую строку менять нельзя — у неё уже есть согласованный
    HR/Manager уровень; чтобы попросить другой, нужно завести новую заявку
    через add_skill (см. _handle_add_skill).

    Если у навыка уже есть подтверждённая строка, новый уровень заявки
    обязан быть строго выше неё — тот же инвариант, что и в add_skill (см.
    _approved_level). Опустить заявку до уровня подтверждённого или ниже
    нельзя — такая строка ничего не отражает, кроме уже согласованного
    факта, её просто нет смысла держать «на рассмотрении».
    """
    user_skill = UserSkill.objects.filter(
        id=request.POST.get("user_skill_id"), user=user, is_approved=False
    ).first()
    level = _parse_level(request.POST.get("level"))

    if not user_skill:
        messages.error(
            request,
            "Заявка не найдена, либо этот навык уже подтверждён — "
            "изменить подтверждённый уровень нельзя, добавьте новую заявку",
        )
        return
    if level is None:
        messages.error(request, "Уровень должен быть от 1 до 4")
        return

    approved_level = _approved_level(user, user_skill.skill)
    if approved_level is not None and level <= approved_level:
        # См. тот же комментарий в _handle_add_skill выше.
        who = "у вас" if user.id == request.user.id else f"у «{user.full_name}»"
        messages.error(
            request,
            f"Уже подтверждён навык «{user_skill.skill.name}» {who} на уровне "
            f"{PROFILE_LEVEL_LABELS[approved_level]} — заявка имеет смысл только на более высокий уровень",
        )
        return

    user_skill.level = level
    user_skill.updated_at = timezone.now()
    user_skill.save(update_fields=["level", "updated_at"])
    messages.success(request, f"Уровень навыка «{user_skill.skill.name}» обновлён")


def _handle_delete_skill(request, user):
    deleted, _ = UserSkill.objects.filter(id=request.POST.get("user_skill_id"), user=user).delete()
    if deleted:
        messages.success(request, "Навык удалён")
    else:
        messages.error(request, "Навык не найден")


def _parse_comment_level(raw_value):
    """Возвращает int оценки (1-3) или None, если значение некорректно."""
    try:
        level = int(raw_value)
    except (TypeError, ValueError):
        return None
    return level if level in COMMENT_LEVEL_LABELS else None


def _can_manage_comments(request_user, profile_user) -> bool:
    """Кто может писать/видеть комментарии о profile_user.

    HR — про любого сотрудника. Manager — только про сотрудников СВОЕГО
    отдела (тот же приём, что и в approvals_page.py/matrix_page.py). Про
    самого себя — никогда и никому, комментарий пишет HR/руководитель о
    сотруднике, не сотрудник сам о себе, и сам объект комментария эти
    заметки не видит вообще (даже если у него по совпадению тоже есть
    роль HR/Manager).
    """
    if request_user.id == profile_user.id:
        return False
    if request_user.has_role("HR"):
        return True
    if request_user.has_role("Manager"):
        return bool(profile_user.department_id) and profile_user.department_id == request_user.department_id
    return False


def _handle_add_comment(request, user):
    if not _can_manage_comments(request.user, user):
        messages.error(request, "Недостаточно прав для добавления комментария")
        return

    text = (request.POST.get("text") or "").strip()
    level = _parse_comment_level(request.POST.get("level"))

    if not text:
        messages.error(request, "Текст комментария не может быть пустым")
        return
    if level is None:
        messages.error(request, "Оценка должна быть от 1 до 3")
        return

    UserComment.objects.create(author=request.user, target_user=user, text=text, level=level)
    messages.success(request, "Комментарий добавлен")


def _handle_update_comment(request, user):
    """Менять комментарий может только его автор (см. _can_manage_comments —
    та проверка тоже нужна: например, если Manager сменил отдел, у него
    больше не должно быть доступа к старым комментариям того отдела)."""
    if not _can_manage_comments(request.user, user):
        messages.error(request, "Недостаточно прав")
        return

    comment = UserComment.objects.filter(
        id=request.POST.get("comment_id"), target_user=user, author=request.user
    ).first()
    text = (request.POST.get("text") or "").strip()
    level = _parse_comment_level(request.POST.get("level"))

    if not comment:
        messages.error(request, "Комментарий не найден, либо вы не его автор")
        return
    if not text:
        messages.error(request, "Текст комментария не может быть пустым")
        return
    if level is None:
        messages.error(request, "Оценка должна быть от 1 до 3")
        return

    comment.text = text
    comment.level = level
    comment.updated_at = timezone.now()
    comment.save(update_fields=["text", "level", "updated_at"])
    messages.success(request, "Комментарий обновлён")


def _handle_delete_comment(request, user):
    if not _can_manage_comments(request.user, user):
        messages.error(request, "Недостаточно прав")
        return

    deleted, _ = UserComment.objects.filter(
        id=request.POST.get("comment_id"), target_user=user, author=request.user
    ).delete()
    if deleted:
        messages.success(request, "Комментарий удалён")
    else:
        messages.error(request, "Комментарий не найден, либо вы не его автор")


ACTION_HANDLERS = {
    "update_profile": _handle_update_profile,
    "update_resume": _handle_update_resume,
    "delete_resume": _handle_delete_resume,
    "add_skill": _handle_add_skill,
    "update_skill": _handle_update_skill,
    "delete_skill": _handle_delete_skill,
    "add_comment": _handle_add_comment,
    "update_comment": _handle_update_comment,
    "delete_comment": _handle_delete_comment,
}

# Куда вернуть пользователя после POST вместо страницы профиля по
# умолчанию — например, reserve.html открывает этот же update_profile
# из "Кадрового резерва" в общем диалоге (см. docstring reserve_page.py),
# и после сохранения логичнее остаться на "Кадровом резерве", а не
# улетать на страницу отредактированного профиля. Передаётся скрытым
# полем формы name="next" со значением ИМЕНИ url'а (не самим URL) —
# сверяем с этим белым списком и вызываем redirect(next_name) только если
# имя в нём есть, чтобы нельзя было передать произвольный редирект.
_ALLOWED_NEXT_URL_NAMES = {"reserve-page"}


def _can_edit(request_user, profile_user) -> bool:
    """Редактировать профиль может сам пользователь, HR — любого, Manager —
    только сотрудников СВОЕГО отдела (тот же приём, что и в
    _can_manage_comments выше: раньше здесь для Manager не было проверки
    отдела вообще, и Manager мог отредактировать/удалить резюме и навыки
    сотрудника из чужого отдела, просто открыв его профиль по id)."""
    if request_user.id == profile_user.id:
        return True
    if request_user.has_role("HR"):
        return True
    if request_user.has_role("Manager"):
        return bool(profile_user.department_id) and profile_user.department_id == request_user.department_id
    return False


@login_required(login_url="/login/")
def profile_page(request, user_id=None):
    if user_id is None:
        user = request.user
    else:
        user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        if not _can_edit(request.user, user):
            return HttpResponseForbidden("Недостаточно прав для редактирования этого профиля")

        handler = ACTION_HANDLERS.get(request.POST.get("action"))
        if handler:
            handler(request, user)
        else:
            messages.error(request, "Неизвестное действие")

        next_url_name = request.POST.get("next")
        if next_url_name in _ALLOWED_NEXT_URL_NAMES:
            return redirect(next_url_name)

        if user_id is None:
            return redirect("my-profile")

        return redirect("profile-page", user_id=user.id)

    user_skills = (
        UserSkill.objects.select_related("skill")
        .prefetch_related("skill__subcategories")
        .filter(user_id=user.id, skill__isnull=False)
        # Подтверждённая строка — первой в паре, чтобы в шаблоне
        # подтверждённый уровень навыка всегда шёл раньше заявки на новый.
        .order_by("skill__name", "-is_approved")
    )

    # Группируем строки по навыку — у одного навыка может быть до двух
    # строк (подтверждённая + заявка на рассмотрении), обе показываем
    # рядом под одним названием навыка (см. docstring UserSkill).
    grouped_skills = {}
    pending_skill_ids = set()
    for us in user_skills:
        if not us.is_approved:
            pending_skill_ids.add(us.skill_id)
        group = grouped_skills.setdefault(
            us.skill_id,
            {
                "skill_id": us.skill_id,
                "display_name": _skill_display_name(us.skill),
                "entries": [],
                # Временное поле, не уходит в шаблон — see ниже, удаляется
                # после цикла. Строки идут approved-первой (order_by выше),
                # так что к моменту обработки заявки этот уровень уже
                # известен.
                "_approved_level": None,
            },
        )
        if us.is_approved:
            group["_approved_level"] = us.level
        group["entries"].append(
            {
                "user_skill_id": us.id,
                "level": us.level,
                "level_label": PROFILE_LEVEL_LABELS.get(us.level, us.level),
                "level_class": PROFILE_LEVEL_LABELS_EN.get(us.level, us.level),
                "is_approved": us.is_approved,
            }
        )

    # Для заявки на рассмотрении в выпадающем списке уровня показываем
    # только уровни СТРОГО ВЫШЕ уже подтверждённого — те же правила, что
    # сервер и так проверит при сохранении (см. _approved_level в
    # _handle_update_skill), просто чтобы пользователь не мог даже выбрать
    # заведомо отклоняемое значение.
    #
    # ЗАПРОС ПОВЫШЕНИЯ ПРЯМО ИЗ СТРОКИ НАВЫКА (по запросу — раньше
    # единственным способом попросить более высокий уровень уже
    # подтверждённого навыка было открыть общий диалог "Добавить навык" и
    # найти там ЭТОТ ЖЕ навык в общем списке — визуально неотличимо от
    # добавления навыка с нуля, сбивало с толку). Теперь: если у навыка
    # есть подтверждённая строка И НЕТ заявки на рассмотрении (т.е.
    # entries содержит только эту одну approved-строку) И есть куда расти
    # (allowed_levels не пуст, т.е. подтверждённый уровень < максимального)
    # — именно у ЭТОЙ approved-строки в upgrade_levels лежит список
    # уровней для инлайн-формы "запросить повышение" (см. profile.html,
    # POST со старым action=add_skill, обработчик не менялся — просто
    # заполняется из другого места разметки). Если заявка уже есть —
    # апгрейд-форма не нужна, у навыка и так уже есть заявка на
    # рассмотрении (это как раз entry с is_approved=False, ниже).
    for group in grouped_skills.values():
        approved_level = group.pop("_approved_level")
        allowed_levels = [
            level for level in sorted(VALID_LEVELS) if approved_level is None or level > approved_level
        ]
        entries = group["entries"]
        has_pending = any(not e["is_approved"] for e in entries)
        for entry in entries:
            if not entry["is_approved"]:
                entry["allowed_levels"] = allowed_levels
            elif not has_pending and allowed_levels:
                entry["upgrade_levels"] = allowed_levels

    # Навык доступен для диалога "Добавить навык", только если у юзера по
    # нему вообще ничего нет — ни заявки, ни подтверждённого уровня.
    # Запрос повышения для уже подтверждённого навыка теперь отдельно, из
    # самой строки навыка (см. upgrade_levels выше) — раньше такие навыки
    # тоже попадали в этот список (см. approved_by_skill ниже, раньше
    # применялся только к подписи уровня внутри диалога через
    # data-approved-level), из-за чего один и тот же навык можно было
    # запросить повышенно ДВУМЯ разными путями — теперь только одним.
    approved_by_skill = {us.skill_id: us.level for us in user_skills if us.is_approved}
    known_skill_ids = pending_skill_ids | set(approved_by_skill.keys())
    available_skills_qs = (
        Skill.objects.filter(is_active=True)
        .exclude(id__in=known_skill_ids)
        .prefetch_related("subcategories")
        .order_by("name")
    )

    projects_qs = (
        UserProject.objects.select_related("project")
        .filter(user_id=user.id)
        .order_by("project__name")
    )
    search = (request.GET.get("search") or "").strip()
    if search:
        projects_qs = projects_qs.filter(project__name__icontains=search)

    # Резюме — файл виден и загружается только HR (см. docstring модуля).
    can_manage_resume = request.user.has_role("HR")

    # Комментарии — HR про любого, Manager только про свой отдел, сам
    # объект комментария их не видит никогда (см. _can_manage_comments).
    can_manage_comments = _can_manage_comments(request.user, user)
    comments = []
    if can_manage_comments:
        comments = [
            {
                "id": c.id,
                "text": c.text,
                "level": c.level,
                "level_label": COMMENT_LEVEL_LABELS.get(c.level, c.level),
                "level_class": COMMENT_LEVEL_CLASS.get(c.level, ""),
                "author_name": c.author.full_name,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "is_mine": c.author_id == request.user.id,
            }
            for c in (
                UserComment.objects.select_related("author")
                .filter(target_user_id=user.id)
                .order_by("-created_at")
            )
        ]

    # См. docstring модуля/_handle_update_profile — HR редактирует чужой
    # (не свой) профиль целиком (кроме фото), а не только phone/city/about.
    hr_editing_other = request.user.has_role("HR") and request.user.id != user.id

    context = {
        "profile_user": user,
        "can_edit": _can_edit(request.user, user),
        "hr_editing_other": hr_editing_other,
        # Для select'а отдела в расширенном диалоге редактирования — нужен
        # только когда hr_editing_other, но передаём всегда без условия,
        # тот же приём, что и в reserve_page.py (там тоже без if вокруг).
        "departments": Department.objects.order_by("name"),
        "departments_str": user.department.name if user.department_id else "—",
        "skills": list(grouped_skills.values()),
        # Раньше тут был ещё "approved_level": approved_by_skill.get(skill.id)
        # для JS-каскада уровней в диалоге (см. data-approved-level в
        # _skill_dialog.html) — available_skills_qs теперь и так исключает
        # все навыки с approved_by_skill (см. выше), значение было бы
        # ВСЕГДА None, поле и сам JS-каскад убраны как мёртвый код.
        "available_skills": [
            {"id": skill.id, "display_name": _skill_display_name(skill)}
            for skill in available_skills_qs
        ],
        "levels": sorted(VALID_LEVELS),
        "projects": [
            {"name": up.project.name,
             "description": up.project.description,
             "icon": f"proj-icons/Project-icon-{randint(1, 5)}.svg",
             "id": up.project.id}
            for up in projects_qs
        ],
        "search": search,
        "can_manage_resume": can_manage_resume,
        "resume_url": user.resume if can_manage_resume else None,
        "can_manage_comments": can_manage_comments,
        "comments": comments,
        "comment_level_choices": sorted(COMMENT_LEVEL_LABELS.items()),
    }
    return render(request, "profile.html", context)
