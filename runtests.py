"""
This code provides a mechanism for running django_ses' internal
test suite without having a full Django project.  It sets up the
global configuration, then dispatches out to `call_command` to
kick off the test suite.

## The Code
"""

# Setup and configure the minimal settings necessary to
# run the test suite.  Note that Django requires that the
# `DATABASES` value be present and configured in order to
# do anything.

import django
from django.conf import settings
from django.core.management import call_command

settings.configure(
    INSTALLED_APPS=[
        "django_ses",
    ],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    MIDDLEWARE_CLASSES=('django.middleware.common.CommonMiddleware',
                        'django.middleware.csrf.CsrfViewMiddleware'),
    ROOT_URLCONF='django_ses.tests.test_urls',
)

django.setup()

# Start the test suite now that the settings are configured.
call_command("test", "django_ses")
