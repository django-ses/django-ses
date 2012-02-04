from django.conf import settings

settings.configure(
    INSTALLED_APPS=[
        "django_ses",
    ],

    # This is required for Django to work
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
from django.core.management import call_command
call_command("test", "django_ses")
