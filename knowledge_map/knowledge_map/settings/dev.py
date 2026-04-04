from .base import *

DEBUG = True
ALLOWED_HOSTS = ['app-aoa-21.devedu.io', 'editor-aoa-21.devedu.io', '127.0.0.1', 'localhost']


#uses the supabase db but will fall back on the sqlite db if something fails
if all([os.getenv("DB_NAME"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST")]):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv("DB_NAME"),
            'USER': os.getenv("DB_USER"),
            'PASSWORD': os.getenv("DB_PASSWORD"),
            'HOST': os.getenv("DB_HOST"),
            'PORT': os.getenv("DB_PORT"),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    
#sqlite db for the testing
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}

# Dev-friendly settings
CSRF_TRUSTED_ORIGINS = [
    'https://*.devedu.io',
    'http://localhost:3000',
    'https://yourknowledgemap.me',
]
