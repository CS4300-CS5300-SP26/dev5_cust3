from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# just for dev
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}