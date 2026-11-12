"""Configurações para os testes automatizados (pytest)."""

import os

os.environ.setdefault("SECRET_KEY", "chave-somente-para-testes")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("SECURE_SSL_REDIRECT", "False")
os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost")

from .settings import *  # noqa: E402,F403

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
WHITENOISE_AUTOREFRESH = True
