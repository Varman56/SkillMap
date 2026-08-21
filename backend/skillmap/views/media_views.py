"""Авторизованная раздача файлов из MEDIA_ROOT (фото/резюме), БЕЗ DRF.

ФИКС по итогам аудита, пункт 1.5: раньше /media/<path> отдавался
напрямую через django.views.static.serve, подключённый в urls.py вообще
без единой проверки авторизации — хотя profile_page.py явно
документирует, что резюме должен видеть и грузить ТОЛЬКО HR (см.
can_manage_resume/_handle_update_resume там же). Прямая ссылка (или
просто перебор имени файла — раньше оно к тому же было предсказуемым,
см. фикс имени файла в profile_page.py._save_uploaded_file) полностью
обходили это ограничение: КТО УГОДНО, даже не залогиненный, мог скачать
чьё угодно резюме или фото.

Под /media/ в проекте лежат только 2 подпапки — photos/ и resumes/ (см.
_save_uploaded_file в profile_page.py, других мест записи в MEDIA_ROOT в
проекте нет) — каждая отдаётся своим view со своей проверкой прав:
- photos/ (serve_photo) — любой авторизованный. Это тот же уровень
  доступа, что и так уже есть у самих страниц (аватарки видны всем
  залогиненным на profile.html/matrix.html/ask.html/reserve.html и
  т.д.) — тут ничего не ужесточаем сверх уже принятой в приложении
  логики, просто закрываем дыру для НЕзалогиненных.
- resumes/ (serve_resume) — только HR, вернёт 403 всем остальным
  (включая Manager и самого сотрудника, чьё это резюме) — ровно то же
  правило, что can_manage_resume в profile_page.py уже применяет к
  ЗАГРУЗКЕ, только теперь настоящее и для ПРОСМОТРА/скачивания тоже.
"""
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponseForbidden


def _safe_path(subdir: str, path: str):
    """Резолвит MEDIA_ROOT/subdir/path в абсолютный Path и возвращает его,
    только если итоговый путь остался ВНУТРИ этой подпапки — иначе None.

    default_storage.save() сам не допустит ".." при сохранении новых
    файлов (см. profile_page.py — там теперь ещё и имя файла случайное,
    не из пользовательского ввода вообще), но path здесь приходит прямо
    из URL запроса, и его никто не гарантирует — явная проверка нужна,
    чтобы GET /media/photos/../../skillmap/settings.py не читал файлы
    вне MEDIA_ROOT/subdir.
    """
    base = (Path(default_storage.location) / subdir).resolve()
    candidate = (base / path).resolve()
    if candidate != base and base not in candidate.parents:
        return None
    return candidate


def _serve(subdir: str, path: str, download: bool = False):
    full_path = _safe_path(subdir, path)
    if full_path is None or not full_path.is_file():
        raise Http404
    # as_attachment=True для резюме — принудительно "Скачать" на уровне
    # самого HTTP-ответа (Content-Disposition), а не только через
    # атрибут download у <a> в profile.html, который ничего не гарантирует,
    # если открыть ссылку напрямую в новой вкладке.
    return FileResponse(open(full_path, "rb"), as_attachment=download, filename=full_path.name)


@login_required(login_url="/login/")
def serve_photo(request, path):
    return _serve("photos", path)


@login_required(login_url="/login/")
def serve_resume(request, path):
    if not request.user.has_role("HR"):
        return HttpResponseForbidden("Недостаточно прав для просмотра резюме")
    return _serve("resumes", path, download=True)
