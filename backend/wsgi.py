"""Shim для NetAngels WSGI.

NetAngels ожидает entry point в `app/wsgi.py` (через переменные APP_PATH/APPLICATION).
Реальное Django-WSGI приложение лежит в `skillmap/wsgi.py`, импортируем его сюда.

Локально этот файл не используется (Django сам через WSGI_APPLICATION находит правильный),
но и не мешает.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from skillmap.wsgi import application

__all__ = ["application"]
