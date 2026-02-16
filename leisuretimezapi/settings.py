"""
Django settings for leisuretimezapi project.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import atexit
import os
from pathlib import Path

import environ

from .wrapper import SSHDBWrapper

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ and read .env file
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

# ---------------------------------------------------------------------------
# PDFShift
# ---------------------------------------------------------------------------

PDFSHIFT_API_KEY = env('PDFSHIFT_API_KEY', default='')

# ---------------------------------------------------------------------------
# Site URLs
# ---------------------------------------------------------------------------

if DEBUG:
    SITE_URL = env('SITE_URL', default='http://localhost:8000')
    FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')
else:
    SITE_URL = env('SITE_URL', default='https://api.leisuretimez.com')
    FRONTEND_URL = env('FRONTEND_URL', default='https://www.leisuretimez.com')

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'django.contrib.humanize',
    'index',
    'myadmin',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/minute' if DEBUG else '30/minute',
        'user': '2000/minute' if DEBUG else '120/minute',
    },
}

# ---------------------------------------------------------------------------
# Caching (used for rate limiting, brute force protection)
# ---------------------------------------------------------------------------

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'leisuretimez-cache',
    }
}

ROOT_URLCONF = 'leisuretimezapi.urls'

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

WSGI_APPLICATION = 'leisuretimezapi.wsgi.application'

AUTH_USER_MODEL = 'index.CustomUser'

# ---------------------------------------------------------------------------
# Database (via SSH tunnel)
# ---------------------------------------------------------------------------

db_wrapper = SSHDBWrapper()
db_wrapper.connect()

DATABASES = {
    'default': db_wrapper.get_database_config()
}

atexit.register(db_wrapper.close)

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
# Static & Media files
# ---------------------------------------------------------------------------

STATIC_URL = 'static/'
STATIC_ROOT = env('STATIC_ROOT', default=str(BASE_DIR / 'static'))
STATICFILES_DIRS = env.list('STATICFILES_DIRS', default=[])

MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = env('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# ---------------------------------------------------------------------------
# Default primary key type
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Email configuration
# ---------------------------------------------------------------------------

if DEBUG:
    # In development, print emails to console instead of sending via SMTP.
    # This lets you see activation links, password reset tokens, etc. in the
    # terminal without needing real SMTP credentials.
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='not-needed-in-dev')
else:
    # In production, use real SMTP. EMAIL_HOST_PASSWORD is required.
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='support@leisuretimez.com')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='support@leisuretimez.com')

# ---------------------------------------------------------------------------
# Development: skip email verification
# ---------------------------------------------------------------------------

# When True, newly registered users are immediately activated (is_active=True)
# so you can register + login + test the full flow without email verification.
# MUST be False in production.
AUTO_ACTIVATE_USERS = env.bool('AUTO_ACTIVATE_USERS', default=DEBUG)

# ---------------------------------------------------------------------------
# Site configuration
# ---------------------------------------------------------------------------

SITE_ID = 1
DOMAIN = 'leisuretimez.com'
SITE_NAME = 'leisuretimez'
ADMIN_EMAIL = env('ADMIN_EMAIL', default='contact@leisuretimez.com')
CONTACT_FROM_EMAIL = env('CONTACT_FROM_EMAIL', default='contact@leisuretimez.com')

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_DIR = env('LOG_DIR', default=str(BASE_DIR / 'logs'))
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'index': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------

if DEBUG:
    # Allow all origins in development for easy API testing (Postman, frontends, etc.)
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
        'https://www.leisuretimez.com',
        'https://leisuretimez.com',
    ])
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Production Security Headers (only enforced when DEBUG=False)
# ---------------------------------------------------------------------------

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
