# cafe_reviews/settings.py
from pathlib import Path
import os
import dj_database_url
from decouple import config
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# === Seguridad / Entorno ===
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    h.strip() for h in config(
        'ALLOWED_HOSTS',
        default='127.0.0.1,localhost,.onrender.com'
    ).split(',')
    if h.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

SECRET_KEY = config('SECRET_KEY', default=None)

def _is_strong_secret(key: str) -> bool:
    return (
        isinstance(key, str)
        and len(key) >= 50
        and not key.startswith('django-insecure-')
        and len(set(key)) >= 5
    )

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = get_random_secret_key()
    else:
        raise RuntimeError(
            "SECRET_KEY no configurada. Definila en el entorno para producción."
        )
elif not DEBUG and not _is_strong_secret(SECRET_KEY):
    raise RuntimeError(
        "SECRET_KEY débil. Generá una clave larga/aleatoria (>=50 chars)."
    )

# === CSRF ===
_csrf_from_env = config('CSRF_TRUSTED_ORIGINS', default=None)
if _csrf_from_env:
    CSRF_TRUSTED_ORIGINS = [
        o.strip() for o in _csrf_from_env.split(',') if o.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']
    if RENDER_EXTERNAL_HOSTNAME:
        CSRF_TRUSTED_ORIGINS.append(
            f"https://{RENDER_EXTERNAL_HOSTNAME}"
        )
    if DEBUG:
        CSRF_TRUSTED_ORIGINS += [
            "http://localhost",
            "http://127.0.0.1",
        ]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config(
    'SECURE_SSL_REDIRECT',
    cast=bool,
    default=not DEBUG
)

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(
        config('SECURE_HSTS_SECONDS', default=31536000)
    )
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "same-origin"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

# === Apps ===
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    # Propias
    'core',
    'accounts.apps.AccountsConfig',
    'reviews.apps.ReviewsConfig',

    # 3rd party
    'rest_framework',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'widget_tweaks',
    'corsheaders',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'cafe_reviews.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'core.context_processors.ui_messages',
        ],
    },
}]

WSGI_APPLICATION = 'cafe_reviews.wsgi.application'

# === DB ===
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}

# === Password validators ===
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# === I18N ===
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']

# === Static / Media ===
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "whitenoise.storage.CompressedStaticFilesStorage"
        )
    },
}

# === User ===
AUTH_USER_MODEL = 'accounts.CustomUser'

# === Sitio ===
SITE_ID = 1
LOGIN_REDIRECT_URL = '/reviews/cafes/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# === Email (SMTP Gmail – FIX CRÍTICO) ===
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

# ⚠️ DEBE coincidir con EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = f"Gota <{EMAIL_HOST_USER}>"

# === allauth ===
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True

ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/accounts/login/"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/reviews/cafes/"

ACCOUNT_SIGNUP_REDIRECT_URL = "/accounts/login/"

ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]

ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m",
    "signup": "3/10m",
    "confirm_email": "3/10m",
    "password_reset": "3/10m",
}


ACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSignupForm'
}

SOCIALACCOUNT_ADAPTER = "accounts.adapters.CustomSocialAccountAdapter"
ACCOUNT_EMAIL_VALIDATORS = [
    "core.validators.validate_not_disposable"
]

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"prompt": "select_account"},
        "APP": {
            "client_id": config("GOOGLE_CLIENT_ID", default=""),
            "secret": config("GOOGLE_CLIENT_SECRET", default=""),
            "key": "",
        },
    }
}

SOCIALACCOUNT_LOGIN_ON_GET = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# === Cache ===
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "gota-local-cache",
    }
}

# === CORS ===
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "https://gotacafe.ar",
    "https://www.gotacafe.ar",
]

# === DRF ===
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

# === Logging ===
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"}
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO"
    },
}
