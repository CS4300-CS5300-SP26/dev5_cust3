from .base import *

#make sure that the env variables are in place for each developer. If not, raise an error
required_env_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
missing = [var for var in required_env_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

DEBUG = False

ALLOWED_HOSTS = ['yourknowledgemap.me', '157.230.89.215', '127.0.0.1', 'localhost']

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

#for when we use a database in deployment, for now we will just use sqlite
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

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://yourknowledgemap.me',
]
