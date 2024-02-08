from .base import *
from decouple import config, Csv

# get the secret key from the environment
SECRET_KEY = config("DJANGO_SECRET_KEY")

# CORS configuration
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv(delimiter=','))
CORS_ALLOW_CREDENTIALS = True

# CSRF configuration
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv(delimiter=','))

# configuration needed for nginx proxy since the connection between nginx and django is unencrypted
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# allowed hosts
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv(delimiter=','))

# setup logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# media files
MEDIA_ROOT = '/media'
MEDIA_URL = '/media/'
STATIC_ROOT = '/static'
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'adare/static_files',
]

# setup secure cookies
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# setup XSS protection
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# redirect all requests to https -> handled by nginx proxy
# if enabled, django is not accessible internally via http (e.g. for gitea webhooks)
SECURE_SSL_REDIRECT = False

# setup HSTS
SECURE_HSTS_SECONDS = 86400  # 1 day
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# Content Security Policy
CSP_DEFAULT_SRC = ("'none'", )
CSP_STYLE_SRC = ("'self'", )
CSP_SCRIPT_SRC = ("'self'", )
CSP_IMG_SRC = ("'self'", )
CSP_FONT_SRC = ("'self'", )


