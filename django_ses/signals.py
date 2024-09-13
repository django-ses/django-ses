from django.dispatch import Signal

from django_ses import models, settings

# The following fields are used from the 3 signals below: mail_obj, bounce_obj, raw_message
bounce_received = Signal()
complaint_received = Signal()
delivery_received = Signal()
send_received = Signal()
open_received = Signal()
click_received = Signal()


def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ENABLE_BOUNCE_BLACKLIST:
        return

    from django_ses.utils import get_permanent_bounced_emails_from_bounce_obj
    bounced_recipients = get_permanent_bounced_emails_from_bounce_obj(bounce_obj)
    for email in bounced_recipients:
        models.BlacklistedEmail.objects.get_or_create(email=email.lower())


def complaint_handler(sender, mail_obj, complaint_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ENABLE_COMPLAINT_BLACKLIST:
        return

    from django_ses.utils import get_emails_from_complaint_obj
    complaint_emails = get_emails_from_complaint_obj(complaint_obj)
    for email in complaint_emails:
        models.BlacklistedEmail.objects.get_or_create(email=email.lower())
