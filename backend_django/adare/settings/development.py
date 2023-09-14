from .base import *

MODE = "development"

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
]
CORS_ALLOW_CREDENTIALS = True

# CSRF CONFIGURATION
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:9000',
    'http://localhost:9001',
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
            "level": "INFO",
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
