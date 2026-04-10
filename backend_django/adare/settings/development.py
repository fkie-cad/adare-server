from .base import *

MODE = "development"

DEBUG = True

SECRET_KEY = 'django-insecure-=1wppni6d7yah@h7f&ieyno$&=_5plu6-u2l=d8^fui67967+#'

# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS = [
    'http://localhost:9000',
    'http://localhost:9001',
    'http://localhost:5173',
    'http://127.0.0.1:9000',
    'http://127.0.0.1:9001',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True

# CSRF CONFIGURATION
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:9000',
    'http://localhost:9001',
    'http://localhost:5173',
    'http://127.0.0.1:9000',
    'http://127.0.0.1:9001',
    'http://127.0.0.1:5173',
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

