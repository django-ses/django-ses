DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'example.db',
    }
}

SECRET_KEY = 'u=0tir)ob&3%uw3h4&&$%!!kffw$h*!_ia46f)qz%2rxnkhak&'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)

ROOT_URLCONF = 'example.urls'

EMAIL_BACKEND = 'django_ses.SESBackend'

from local_settings import *

