"""
Test cases for the provided signal handlers.
"""

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.test import TestCase

from django_ses.models import (
    SESBounce,
    BouncedRecipient,
    SESComplaint,
    ComplainedRecipient
)
from django_ses.handlers import (
    log_bounce_to_db,
    log_complaint_to_db,
)

__all__ = (
    'BounceHandlerTest',
    'ComplaintHandlerTest',
)

class BounceHandlerTest(TestCase):
    """
    Tests for the provided log_bounce_to_db handler.
    """
    def setUp(self):
        pass

    def test_normal_bounce(self):
        """
        Tests handling a standard bounce message.
        """
        req_mail_obj = {
            "timestamp":"2012-05-25T14:59:38.623-07:00",
            "messageId":"000001378603177f-7a5433e7-8edb-42ae-af10-f0181f34d6ee-000000",
            "source":"sender@example.com",
            "destination":[
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com",
                "recipient4@example.com"
            ]
        }
        req_bounce_obj = {
            'bounceType': 'Permanent',
            'bounceSubType': 'General',
            'bouncedRecipients': [
                {
                    "status":"5.0.0",
                    "action":"failed",
                    "diagnosticCode":"smtp; 550 user unknown",
                    "emailAddress":"recipient1@example.com",
                }, 
                {
                    "status":"4.0.0",
                    "action":"delayed",
                    "emailAddress":"recipient2@example.com",
                }
            ],
            "reportingMTA": "example.com",
            "timestamp":"2012-05-25T14:59:38.605-07:00",
            "feedbackId":"000001378603176d-5a4b5ad9-6f30-4198-a8c3-b1eb0c270a1d-000000",
        }
        message = {
            'notificationType': 'Bounce',
            'mail': req_mail_obj,
            'bounce': req_bounce_obj,
        }

        log_bounce_to_db(
            sender=SESBounce,
            mail_obj=req_mail_obj,
            bounce_obj=req_bounce_obj,
            raw_message=json.dumps(message),
        )

        self.assertEquals(SESBounce.objects.count(), 1)

class ComplaintHandlerTest(TestCase):
    """
    Tests for the provided log_complaint_to_db handler.
    """
    def setUp(self):
        pass

    def test_normal_complaint(self):
        """
        Tests handling a standard complaint message.
        """
        req_mail_obj = {
            "timestamp":"2012-05-25T14:59:38.623-07:00",
            "messageId":"000001378603177f-7a5433e7-8edb-42ae-af10-f0181f34d6ee-000000",
            "source":"sender@example.com",
            "destination": [
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com",
                "recipient4@example.com",
            ]
        }
        req_complaint_obj = {
            "userAgent":"Comcast Feedback Loop (V0.01)",
            "complainedRecipients": [
                {
                    "emailAddress":"recipient1@example.com",
                }
            ],
            "complaintFeedbackType":"abuse",
            "arrivalDate":"2009-12-03T04:24:21.000-05:00",
            "timestamp":"2012-05-25T14:59:38.623-07:00",
            "feedbackId":"000001378603177f-18c07c78-fa81-4a58-9dd1-fedc3cb8f49a-000000",
        }
        message = {
            'notificationType': 'Complaint',  
            'mail': req_mail_obj,
            'complaint': req_complaint_obj,
        }

        log_complaint_to_db(
            sender=SESBounce,
            mail_obj=req_mail_obj,
            complaint_obj=req_complaint_obj,
            raw_message=json.dumps(message),
        )

        self.assertEquals(SESComplaint.objects.count(), 1)
