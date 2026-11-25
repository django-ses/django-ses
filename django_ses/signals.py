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


def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ADD_BOUNCE_TO_BLACKLIST:
        return

    from django_ses.utils import (
        blacklist_recipients,
        get_bounce_reason,
        get_permanent_bounced_recipients_from_bounce_obj,
    )

    bounced_recipients = get_permanent_bounced_recipients_from_bounce_obj(bounce_obj)
    blacklist_recipients({br.get("emailAddress"): get_bounce_reason(bounce_obj, br) for br in bounced_recipients})


def complaint_handler(sender, mail_obj, complaint_obj, raw_message, *args, **kwargs):
    if not settings.AWS_SES_ADD_COMPLAINT_TO_BLACKLIST:
        return

    from django_ses.utils import blacklist_recipients, get_complaint_reason, get_emails_from_complaint_obj

    reason = get_complaint_reason(complaint_obj)
    blacklist_recipients({email: reason for email in get_emails_from_complaint_obj(complaint_obj)})
