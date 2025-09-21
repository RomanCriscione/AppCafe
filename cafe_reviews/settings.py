from pathlib import Path
import os
import dj_database_url
from decouple import config
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# === Seguridad / Entorno ===
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    h.strip() for h in config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')
    if h.strip()
]

SECRET_KEY = config('SECRET_KEY', default=None)

def _is_strong_secret(key: str) -> bool:
    return isinstance(key, str) and len(key) >= 50 and not key.startswith('django-insecure-') and len(set(key)) >= 5

if not SECRET_KEY:
    if DEBUG:
        # Dev fallback (no usar en prod)
        SECRET_KEY = get_random_secret_key()
    else:
        raise RuntimeError("SECRET_KEY no configurada. Definila en el entorno para producción.")
elif not DEBUG and not _is_strong_secret(SECRET_KEY):
    raise RuntimeError("SECRET_KEY débil. Generá una clave larga/aleatoria (>=50 chars).")

# CSRF Trusted Origins (si no se provee env, se derivan de ALLOWED_HOSTS)
_csrf_from_env = config('CSRF_TRUSTED_ORIGINS', default=None)
if _csrf_from_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_from_env.split(',') if o.strip()]
else:
    schemes = ['https'] if not DEBUG else ['http', 'https']
    CSRF_TRUSTED_ORIGINS = [
        f"{scheme}://{host}" for scheme in schemes for host in ALLOWED_HOSTS if host and host != '*'
    ]

# Detrás de proxy (Heroku/Render/Nginx con X-Forwarded-Proto)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS (activá esto solo si todo el sitio va 100% por HTTPS)
    SECURE_HSTS_SECONDS = int(config('SECURE_HSTS_SECONDS', default=31536000))  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Endurecimiento adicional recomendado
    SECURE_REFERRER_POLICY = "same-origin"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

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

    # Apps propias
    'core',
    'accounts',
    'reviews.apps.ReviewsConfig',

    # 3rd party
    'rest_framework',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'widget_tweaks',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # estático en prod
    'django.contrib.sessions.middleware.SessionMiddleware',
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
    'DIRS': [os.path.join(BASE_DIR, 'templates')],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',  # requerido por allauth
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'core.context_processors.ui_messages',
        ],
    },
}]

WSGI_APPLICATION = 'cafe_reviews.wsgi.application'

# === DB ===
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
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

# === Static/Media ===
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "static"]
else:
    STATICFILES_DIRS = []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django 5: STORAGES (sin STATICFILES_STORAGE legacy)
if DEBUG:
    static_backend = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    static_backend = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": static_backend},
}

# === User model ===
AUTH_USER_MODEL = 'accounts.CustomUser'

# === Sitio / Redirecciones ===
SITE_ID = 1
LOGIN_REDIRECT_URL = '/reviews/cafes/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# === Email ===
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default="no-reply@gota.local")

# === allauth ===
ACCOUNT_EMAIL_VERIFICATION = config('ACCOUNT_EMAIL_VERIFICATION', default="optional")
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_RATE_LIMITS = {"login_failed": "5/5m"}

ACCOUNT_FORMS = {'signup': 'accounts.forms.CustomSignupForm'}
ACCOUNT_EMAIL_VALIDATORS = ["core.validators.validate_not_disposable"]

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

# === Planes / Upgrades ===
PLAN_UPGRADES_ENABLED = False
PAYMENT_LINKS = {
    1: "https://tu-pasarela.com/checkout/plan-barista",
    2: "https://tu-pasarela.com/checkout/plan-maestro",
}
