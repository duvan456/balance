from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-change-this-in-production"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "tasks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

MOVEMENT_PAGE_SIZE_MAX = int(os.getenv("MOVEMENT_PAGE_SIZE_MAX", "100"))
MOVEMENT_EXPORT_MAX_ROWS = int(os.getenv("MOVEMENT_EXPORT_MAX_ROWS", "500000"))

FABRIC_WAREHOUSE_SERVER = os.getenv(
    "FABRIC_WAREHOUSE_SERVER",
    "gh5sughwadpurfndk6z762tuuq-fvbqi3ipc7nuxhuw4ucuzeepkm.datawarehouse.fabric.microsoft.com",
)
FABRIC_WAREHOUSE_DATABASE = os.getenv("FABRIC_WAREHOUSE_DATABASE", "Financiera")
FABRIC_WAREHOUSE_ODBC_DRIVER = os.getenv(
    "FABRIC_WAREHOUSE_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"
)
FABRIC_WAREHOUSE_AUTHENTICATION = os.getenv(
    "FABRIC_WAREHOUSE_AUTHENTICATION", "ActiveDirectoryInteractive"
)
