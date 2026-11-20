from django.db import NotSupportedError
from django.dispatch import Signal

from django_ses.conf import settings

# The following fields are used from the 3 signals below: mail_obj, bounce_obj, raw_message
message_sent = Signal()
bounce_received = Signal()
complaint_received = Signal()
delivery_received = Signal()
send_received = Signal()
open_received = Signal()
click_received = Signal()


def _blacklist_recipients(reasons):
    """Blacklists each email in ``reasons``, a dict that maps an email to why it is blacklisted.

    An email that is already blacklisted keeps the reason it was first blacklisted for.
    """
    from django_ses import models

    reasons = {email.lower(): reason for email, reason in reasons.items() if email}
    if len(reasons) == 0:
        return

    # If we received only 1 recipients, don't waste extra queries trying to find
    # out if the recipient has already been blacklisted; just attempt to
    # blacklist it.
    if len(reasons) == 1:
        ((email, reason),) = reasons.items()
        models.BlacklistedEmail.objects.get_or_create(email=email, defaults={"reason": reason})
        return

    qs = models.BlacklistedEmail.objects.filter(email__in=reasons)
    blacklisted_emails = set(qs.values_list("email", flat=True))
    unblacklisted_emails = [email for email in reasons if email not in blacklisted_emails]

    # Try to bulk-insert the unblacklisted emails. If the operation fails (a
    # possibility only when using Oracle because it doesn't support
    # ignore_conflicts), fallback to one-by-one insertion.
    try:
        models.BlacklistedEmail.objects.bulk_create(
            [models.BlacklistedEmail(email=email, reason=reasons[email]) for email in unblacklisted_emails],
            ignore_conflicts=True,
        )
    except NotSupportedError:  # Oracle doesn't support "ignore_conflicts"
        for email, reason in reasons.items():
            models.BlacklistedEmail.objects.get_or_create(email=email, defaults={"reason": reason})


def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ADD_BOUNCE_TO_BLACKLIST:
        return

    from django_ses.utils import get_bounce_reason, get_permanent_bounced_recipients_from_bounce_obj

    bounced_recipients = get_permanent_bounced_recipients_from_bounce_obj(bounce_obj)
    _blacklist_recipients({br.get("emailAddress"): get_bounce_reason(bounce_obj, br) for br in bounced_recipients})


def complaint_handler(sender, mail_obj, complaint_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ADD_COMPLAINT_TO_BLACKLIST:
        return

    from django_ses.utils import get_complaint_reason, get_emails_from_complaint_obj

    reason = get_complaint_reason(complaint_obj)
    _blacklist_recipients({email: reason for email in get_emails_from_complaint_obj(complaint_obj)})
