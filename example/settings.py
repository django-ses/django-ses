import os

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
    'middleware.FakeSuperuserMiddleware',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django_ses',
)

ROOT_URLCONF = 'example.urls'

EMAIL_BACKEND = 'django_ses.SESBackend'

from local_settings import *

