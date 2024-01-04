from .base import *

MODE = "development"

DEBUG = True

# DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db.sqlite3',
    }
}

# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS = [
    'http://localhost:9000',
    'http://localhost:9001',
    'http://127.0.0.1:9000',
    'http://127.0.0.1:9001',
]
CORS_ALLOW_CREDENTIALS = True

# CSRF CONFIGURATION
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:9000',
    'http://localhost:9001',
    'http://127.0.0.1:9000',
    'http://127.0.0.1:9001',
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "NOTSET",
        },
    }
}

# media files
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / 'static'
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'adare/static_files',
]

# social auth credentials (for development only)
FRONTEND_URL = 'http://localhost:9000'

SOCIALACCOUNT_PROVIDERS = {
    'gitea': {
        'GITEA_URL': 'https://adare.seclab-bonn.de/git/',
        'VERIFIED_EMAIL': False,
        'APP': {
            'client_id': '3b02bfda-9629-44bd-9d62-747a57da883f',
            'secret': 'gto_zdvsyee5hvbzpwwwascnxeedpo5ytbvuftriokde73ey3hu2fdyq',
            'key': ''
        },
    }
}