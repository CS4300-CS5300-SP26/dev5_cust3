from .base import *

DEBUG = False

ALLOWED_HOSTS = ['yourknowledgemap.me', '157.230.89.215']

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

#sqlite db for the testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://yourknowledgemap.me',
]
