from django.apps import AppConfig


class DjangoSESConfig(AppConfig):
    name = 'django_ses'
    verbose_name = 'Django SES'

    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        # Explicitly connect signal handlers decorated with @receiver.
        from django_ses.signals import (
            bounce_handler,
            bounce_received,
            complaint_handler,
            complaint_received,
        )
        bounce_received.connect(bounce_handler)
        complaint_received.connect(complaint_handler)
