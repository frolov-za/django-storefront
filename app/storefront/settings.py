from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    """Read a conventional boolean value from the environment."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
DEBUG = env_bool('DEBUG', default=True)
ALLOWED_HOSTS = ['.localhost', '127.0.0.1', '.ngrok-free.app', 'storefront.local', 'storefront.netbird.cloud']
CSRF_TRUSTED_ORIGINS = [
    "https://127.0.0.1",
    "https://storefront.local",  
    "http://127.0.0.1",
    "http://storefront.local",
    "https://storefront.netbird.cloud",]

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'

TIME_ZONE = 'Europe/Moscow'
USE_TZ = True

LOGOUT_REDIRECT_URL = '/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'products',
    'label_printer.apps.LabelPrinterConfig',
    'cropperjs',
    'django_cleanup.apps.CleanupConfig',
    'pwa',
    'django_celery_beat',
]

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # результат collectstatic
STATICFILES_DIRS = [
   os.path.join(BASE_DIR, "static"),
]


#PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/js', 'serviceworker.js')
PWA_APP_NAME = 'StoreFront'
PWA_APP_DESCRIPTION = "StoreFront печать этикеток"
PWA_APP_THEME_COLOR = '#0A0302'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_LANG = 'ru-RU'
PWA_APP_ICONS = [
    {
        'src': STATIC_URL + 'img/logo-160x160.png',
        'sizes': '160x160'
    },
    {
        'src': STATIC_URL + 'img/logo-512x512.png',
        'sizes': '512x512'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': STATIC_URL + 'img/logo-512x512.png',
        'sizes': '512x512'
    }
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'storefront.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'templates')],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'storefront.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('SQLITE_PATH', BASE_DIR / 'db.sqlite3'),
    }
}

ALLOWED_SHELL_COMMANDS = ['ls /dev/usb/lp*']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '{asctime} [{levelname}] [{name}:{lineno}] {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },

        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'encoding': 'utf-8',
            'formatter': 'default',
        },
    },

    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG' if DEBUG else 'INFO',
    },
}

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TIMEZONE = TIME_ZONE
