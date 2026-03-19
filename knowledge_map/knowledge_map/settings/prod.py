from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['yourknowledgemap.me', '24.144.92.128']

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

#for when we use a database in deployment, for now we will just use sqlite
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': os.getenv("DB_NAME"),
#        'USER': os.getenv("DB_USER"),
#        'PASSWORD': os.getenv("DB_PASSWORD"),
#        'HOST': os.getenv("DB_HOST"),
#        'PORT': os.getenv("DB_PORT"),
#    }
#}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# (default is dev file)
# for production please use:
#export DJANGO_SETTINGS_MODULE=knowledge_map.settings.prod
#gunicorn knowledge_map.wsgi