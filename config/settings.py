"""Configurações do projeto Ágape Conecta.

Valores sensíveis e dependentes do ambiente (SECRET_KEY, DEBUG, banco de dados,
hosts permitidos) são lidos de variáveis de ambiente, nunca do código-fonte.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(nome, padrao=False):
    return os.environ.get(nome, str(padrao)).strip().lower() in {"1", "true", "sim", "yes"}


DEBUG = env_bool("DEBUG", False)

# Em desenvolvimento uma chave local é aceita; em produção a variável é obrigatória.
SECRET_KEY = os.environ.get("SECRET_KEY") or (
    "chave-apenas-para-desenvolvimento-local" if DEBUG else None
)
if not SECRET_KEY:
    raise RuntimeError("Defina a variável de ambiente SECRET_KEY.")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "contas",
    "gestao",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Banco: PostgreSQL via DATABASE_URL; sem a variável, usa SQLite apenas para desenvolvimento local.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
# Compatível com o pooler de conexões do Neon (PgBouncer em modo transação).
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

AUTH_USER_MODEL = "contas.Usuario"

# Senhas: Argon2id como algoritmo principal (nunca texto limpo, MD5 ou SHA-1).
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "contas:login"
LOGIN_REDIRECT_URL = "gestao:painel"
LOGOUT_REDIRECT_URL = "contas:login"

# Sessão: expira após 30 minutos sem uso; cookies inacessíveis a scripts.
SESSION_COOKIE_AGE = 30 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Bloqueio de login: tentativas inválidas por e-mail dentro da janela.
LOGIN_MAX_TENTATIVAS = 5
LOGIN_JANELA_SEGUNDOS = 15 * 60

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # A hospedagem usa subdomínio do provedor, que não controlamos; por isso não
    # ativamos includeSubDomains nem preload do HSTS (decisão consciente).
    SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]
    # Em produção a aplicação pode rodar em várias instâncias (ex.: funções da Vercel).
    # O cache fica no banco para que o bloqueio de login valha para todas elas.
    # Crie a tabela uma vez com: python manage.py createcachetable
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "cache_aplicacao",
        }
    }

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
