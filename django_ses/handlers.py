"""
Signal handlers for django-ses

These signal handlers are provided as is and are not
connected to signal dispatch automatically. You will
need to connect them in your application.

::

    from django_ses.signals import bounce_received, complaint_received
    from django_ses.handlers import log_bounces_to_db, log_complaints_to_db

    bounce_received.connect(log_bounce_to_db)
    complaint_received.connect(log_complaint_to_db)
"""

from django.db import transaction
from django_ses.models import (
    SESBounce, BouncedRecipient,
    SESComplaint, ComplainedRecipient,
)

try:
    from iso8601 import parse_date
except ImportError:
    try:
        from dateutil.parser import parse as parse_date
    except ImportError:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("django-ses signal handlers require pyiso8601 or dateutil to be installed.")

__all__ = (
    'log_bounce_to_db',
    'log_complaint_to_db',
)

def _parse_date(dt):
    # Strip tzinfo data before saving because some database backends
    # do not support datetime objects with timezone info.
    return parse_date(dt).replace(tzinfo=None)

@transaction.commit_on_success
def log_bounce_to_db(sender, *args, **kwargs):
    """
    A signal handler that logs bounces to the DB.

    To use it connect this handler to the bounce_received signal
    in your application.
    """
    mail_obj = kwargs['mail_obj']
    bounce_obj = kwargs['bounce_obj']

    bounce = SESBounce.objects.create(
        timestamp=_parse_date(mail_obj['timestamp']),
        message_id=mail_obj.get('timestamp'),
        source=mail_obj['source'],
        destination=",".join(mail_obj['destination']),

        bounce_type=bounce_obj['bounceType'], 
        bounce_subtype=bounce_obj['bounceSubType'], 
        bounce_timestamp=_parse_date(bounce_obj['timestamp']),
        feedback_id=bounce_obj['feedbackId'], 
    )

    for recipient in bounce_obj.get('bouncedRecipients', []): 
        BouncedRecipient.objects.create(
            bounce=bounce,
            email_address=recipient['emailAddress'],
            action=recipient.get('action'),
        )

@transaction.commit_on_success
def log_complaint_to_db(sender, *args, **kwargs):
    """
    A signal handler that logs complaints to the DB.

    To use it connect this handler to the complaint_received signal
    in your application.
    """
    mail_obj = kwargs['mail_obj']
    complaint_obj = kwargs['complaint_obj']

    arrival_date = complaint_obj.get('arrivalDate')
    if arrival_date:
        arrival_date = _parse_date(arrival_date)

    complaint = SESComplaint.objects.create(
        timestamp=_parse_date(mail_obj['timestamp']),
        message_id=mail_obj['messageId'],
        source=mail_obj['source'],
        destination=",".join(mail_obj['destination']),

        feedback_id=complaint_obj['feedbackId'], 
        complaint_timestamp=_parse_date(complaint_obj['timestamp']),
        user_agent=complaint_obj.get('userAgent'),
        complaint_feedback_type=complaint_obj.get('complaintFeedbackType'),
        arrival_date=arrival_date,
    )
    
    for recipient in complaint_obj.get('complainedRecipients', []): 
        ComplainedRecipient.objects.create(
            complaint=complaint,
            email_address=recipient['emailAddress'],
        )
