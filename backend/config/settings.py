"""
Django settings for the AI-Powered E-commerce backend.

Configuration is organized into clearly labelled sections. Secrets and
environment-specific values are NOT hardcoded here — they are read from a
`.env` file via `python-decouple` (see the `.env.example` template).
"""

from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

# BASE_DIR points at the `backend/` folder (two levels up from this file).
# We build other paths relative to it, e.g. BASE_DIR / 'db.sqlite3'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Core security settings (read from .env)
# ---------------------------------------------------------------------------
# `config('NAME')` reads the variable NAME from the .env file (or the real
# environment). The second argument is a fallback/default used in development.

SECRET_KEY = config('SECRET_KEY')

# DEBUG must be False in production. `cast=bool` converts the string "True"
# from .env into a real Python boolean.
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts/domains this site is allowed to serve. Csv() turns a comma-separated
# string ("localhost,127.0.0.1") into a Python list.
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "10.10.0.36",
]


# ---------------------------------------------------------------------------
# Installed applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Third-party packages we installed.
THIRD_PARTY_APPS = [
    'rest_framework',        # Django REST Framework (API toolkit)
    'rest_framework_simplejwt.token_blacklist',  # enables logout (blacklist refresh tokens)
    'corsheaders',           # Cross-Origin Resource Sharing for the React app
    'django_filters',        # Advanced filtering for list endpoints (Phase 3)
]

# Our own apps. Each one is added in the phase that introduces it so the
# project always stays runnable.
LOCAL_APPS = [
    'accounts',     # Phase 2 — authentication & user profiles
    'products',     # Phase 3 — catalog
    'orders',       # Phase 4 — cart & orders
    'assistant',    # Phase 7 — AI chatbot
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
# Order matters. CorsMiddleware must come high up, before CommonMiddleware,
# so it can add CORS headers to every response.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------------------------------------
# Database — SQLite for development (easy, file-based, zero setup)
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
# STATIC = CSS/JS served by Django. MEDIA = user-uploaded files (product images).
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tell Django to use our custom user model instead of the built-in auth.User.
# This MUST be set before the very first migration that creates the user table.
AUTH_USER_MODEL = 'accounts.User'


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
# These are project-wide defaults. We make JWT the default authentication
# method and require authentication unless a view explicitly opts out.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
    # Rate limit for the AI assistant endpoint (protects the shared local LLM).
    # Only views that opt into the 'assistant' scope are affected.
    'DEFAULT_THROTTLE_RATES': {
        'assistant': '20/min',
    },
}


# ---------------------------------------------------------------------------
# SimpleJWT — token lifetimes
# ---------------------------------------------------------------------------
# Access tokens are short-lived (sent with every request). Refresh tokens are
# long-lived and used to obtain a new access token without logging in again.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_DAYS', default=7, cast=int)),

    # When a refresh token is used, issue a brand-new refresh token too...
    'ROTATE_REFRESH_TOKENS': True,
    # ...and blacklist the old one so it can't be reused. Combined with the
    # token_blacklist app, this is what makes logout actually work.
    'BLACKLIST_AFTER_ROTATION': True,
}


# ---------------------------------------------------------------------------
# CORS — allow the React dev server to call this API
# ---------------------------------------------------------------------------
# During development React runs on http://localhost:3000. We whitelist it here.
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv(),
)


# ---------------------------------------------------------------------------
# Ollama (local LLM) — used by the AI assistant in Phase 6
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = config('OLLAMA_BASE_URL', default='http://localhost:11434')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='llama3')
