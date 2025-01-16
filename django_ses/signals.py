from django.db import NotSupportedError
from django.dispatch import Signal

from django_ses import settings

# The following fields are used from the 3 signals below: mail_obj, bounce_obj, raw_message
message_sent = Signal()
bounce_received = Signal()
complaint_received = Signal()
delivery_received = Signal()
send_received = Signal()
open_received = Signal()
click_received = Signal()


def _blacklist_recipients(recipients):
    from django_ses import models

    if len(recipients) == 0:
        return

    recipients = [email.lower() for email in recipients]

    # If we received only 1 recipients, don't waste extra queries trying to find
    # out if the recipient has already been blacklisted; just attempt to
    # blacklist it.
    if len(recipients) == 1:
        models.BlacklistedEmail.objects.get_or_create(email=recipients[0])
        return

    qs = models.BlacklistedEmail.objects.filter(email__in=recipients)
    blacklisted_emails = set(qs.values_list("email", flat=True))
    unblacklisted_emails = [email for email in recipients if email not in blacklisted_emails]

    # Try to bulk-insert the unblacklisted emails. If the operation fails (a
    # possibility only when using Oracle because it doesn't support
    # ignore_conflicts), fallback to one-by-one insertion.
    try:
        models.BlacklistedEmail.objects.bulk_create([
            models.BlacklistedEmail(email=email) for email in unblacklisted_emails
        ], ignore_conflicts=True)
    except NotSupportedError: # Oracle doesn't support "ignore_conflicts"
        for email in recipients:
            models.BlacklistedEmail.objects.get_or_create(email=email)


def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ADD_BOUNCE_TO_BLACKLIST:
        return

    from django_ses.utils import get_permanent_bounced_emails_from_bounce_obj
    bounced_recipients = get_permanent_bounced_emails_from_bounce_obj(bounce_obj)
    _blacklist_recipients(bounced_recipients)


def complaint_handler(sender, mail_obj, complaint_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ADD_COMPLAINT_TO_BLACKLIST:
        return

    from django_ses.utils import get_emails_from_complaint_obj
    complaint_emails = get_emails_from_complaint_obj(complaint_obj)
    _blacklist_recipients(complaint_emails)
