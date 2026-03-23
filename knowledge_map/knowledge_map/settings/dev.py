from .base import *

DEBUG = True

ALLOWED_HOSTS = []

# Use SQLite locally (what you already have)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Dev-friendly settings
CSRF_TRUSTED_ORIGINS = [
    'https://*.devedu.io',
    'http://localhost:3000',
    'https://yourknowledgemap.me',
]
