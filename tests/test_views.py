import json

try:
    from unittest import mock
except ImportError:
    import mock

from django.test import TestCase
from django.urls import reverse

from django_ses.signals import bounce_received, complaint_received, send_received, delivery_received, open_received, \
    click_received
from django_ses import utils as ses_utils


def get_mock_email():
    return {
        "timestamp": "2012-05-25T14:59:38.623-07:00",
        "messageId": "000001378603177f-7a5433e7-8edb-42ae-af10-f0181f34d6ee-000000",
        "source": "sender@example.com",
        "destination": [
            "recipient1@example.com",
            "recipient2@example.com",
            "recipient3@example.com",
            "recipient4@example.com"
        ]
    }


def get_mock_notification(message):
    return {
        "Type": "Notification",
        "MessageId": "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyTopic",
        "Subject": "Amazon SES Email Event Notification",
        "Message": json.dumps(message),
        "Timestamp": "2012-05-02T00:54:06.655Z",
        "SignatureVersion": "1",
        "Signature": "",
        "SigningCertURL": "",
        "UnsubscribeURL": ""
    }


def get_mock_bounce():
    mail = get_mock_email()
    bounce = {
        "bounceType": "Permanent",
        "bounceSubType": "General",
        "bouncedRecipients": [
            {
                "status": "5.0.0",
                "action": "failed",
                "diagnosticCode": "smtp; 550 user unknown",
                "emailAddress": "recipient1@example.com",
            },
            {
                "status": "4.0.0",
                "action": "delayed",
                "emailAddress": "recipient2@example.com",
            }
        ],
        "reportingMTA": "example.com",
        "timestamp": "2012-05-25T14:59:38.605-07:00",
        "feedbackId": "000001378603176d-5a4b5ad9-6f30-4198-a8c3-b1eb0c270a1d-000000",
    }

    message = {
        "eventType": "Bounce",
        "mail": mail,
        "bounce": bounce,
    }
    notification = get_mock_notification(message)
    return mail, bounce, notification


def get_mock_send():
    mail = get_mock_email()
    send = {}
    message = {
        "eventType": "Send",
        "mail": mail,
        "send": send,
    }
    notification = get_mock_notification(message)
    return mail, send, notification


def get_mock_delivery():
    mail = get_mock_email()
    delivery = {
        "timestamp": "2021-01-26T14:38:39.270Z",
        "processingTimeMillis": 1796,
        "recipients": ["recipient1@example.com"],
        "smtpResponse": "",
        "reportingMTA": ""
    }
    message = {
        "eventType": "Delivery",
        "mail": mail,
        "delivery": delivery,
    }
    notification = get_mock_notification(message)
    return mail, delivery, notification


def get_mock_open():
    mail = get_mock_email()
    open = {
        "timestamp": "2021-01-26T14:38:52.115Z",
        "userAgent": "Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0 (via ggpht.com GoogleImageProxy)",
        "ipAddress": "11.111.11.111"
    }
    message = {
        "eventType": "Open",
        "mail": mail,
        "open": open,
    }
    notification = get_mock_notification(message)
    return mail, open, notification


def get_mock_click():
    mail = get_mock_email()
    click = {
        "timestamp": "2021-01-26T14:38:55.540Z",
        "ipAddress": "11.111.11.111",
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        "link": "github.com/django-ses/django-ses",
        "linkTags": None
    }
    message = {
        "eventType": "Click",
        "mail": mail,
        "click": click,
    }
    notification = get_mock_notification(message)
    return mail, click, notification


class HandleBounceTestCase(TestCase):
    """
    Test the bounce web hook handler.
    """
    def setUp(self):
        self._old_bounce_receivers = bounce_received.receivers
        bounce_received.receivers = []

        self._old_complaint_receivers = complaint_received.receivers
        complaint_received.receivers = []

    def tearDown(self):
        bounce_received.receivers = self._old_bounce_receivers
        complaint_received.receivers = self._old_complaint_receivers

    def test_handle_bounce(self):
        """
        Test handling a normal bounce request.
        """
        req_mail_obj, req_bounce_obj, notification = get_mock_bounce()

        def _handler(sender, mail_obj, bounce_obj, raw_message, **kwargs):
            _handler.call_count += 1
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_bounce_obj, bounce_obj)
            self.assertEqual(raw_message, json.dumps(notification).encode())
        _handler.call_count = 0
        bounce_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, "verify_event_message") as verify:
            verify.return_value = True

            response = self.client.post(reverse("django_ses_bounce"), json.dumps(notification), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)


class HandleEventTestCase(TestCase):
    """
    Test the event web hook handler.
    """
    def setUp(self):
        self._old_bounce_receivers = bounce_received.receivers
        bounce_received.receivers = []

        self._old_complaint_receivers = complaint_received.receivers
        complaint_received.receivers = []

    def tearDown(self):
        bounce_received.receivers = self._old_bounce_receivers
        complaint_received.receivers = self._old_complaint_receivers

    def test_handle_bounce_event(self):
        """
        Test handling a normal bounce request.
        """
        req_mail_obj, req_bounce_obj, notification = get_mock_bounce()

        def _handler(sender, mail_obj, bounce_obj, raw_message, **kwargs):
            _handler.call_count += 1
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_bounce_obj, bounce_obj)
            self.assertEqual(raw_message, json.dumps(notification).encode())
        _handler.call_count = 0
        bounce_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, "verify_event_message") as verify:
            verify.return_value = True
            response = self.client.post(reverse("event_webhook"), json.dumps(notification), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)

    def test_handle_send_event(self):
        """
        Test handling a send event request.
        """
        req_mail_obj, req_send_obj, notification = get_mock_send()

        def _handler(sender, mail_obj, send_obj, raw_message, **kwargs):
            _handler.call_count += 1
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_send_obj, send_obj)
            self.assertEqual(raw_message, json.dumps(notification).encode())
        _handler.call_count = 0
        send_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, "verify_event_message") as verify:
            verify.return_value = True
            response = self.client.post(reverse("event_webhook"), json.dumps(notification), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)

    def test_handle_delivery_event(self):
        """
        Test handling a delivery event request.
        """
        req_mail_obj, req_delivery_obj, notification = get_mock_delivery()

        def _handler(sender, mail_obj, delivery_obj, raw_message, **kwargs):
            _handler.call_count += 1
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_delivery_obj, delivery_obj)
            self.assertEqual(raw_message, json.dumps(notification).encode())
        _handler.call_count = 0
        delivery_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, "verify_event_message") as verify:
            verify.return_value = True
            response = self.client.post(reverse("event_webhook"), json.dumps(notification), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)

    def test_handle_open_event(self):
        """
        Test handling a open event request.
        """
        req_mail_obj, req_open_obj, notification = get_mock_open()

        def _handler(sender, mail_obj, open_obj, raw_message, **kwargs):
            _handler.call_count += 1
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_open_obj, open_obj)
            self.assertEqual(raw_message, json.dumps(notification).encode())
        _handler.call_count = 0
        open_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, "verify_event_message") as verify:
            verify.return_value = True
            response = self.client.post(reverse("event_webhook"), json.dumps(notification), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)

    def test_handle_click_event(self):
        """
        Test handling a click event request.
        """
        req_mail_obj, req_click_obj, notification = get_mock_click()

        def _handler(sender, mail_obj, click_obj, raw_message, **kwargs):
            _handler.call_count += 1
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_click_obj, click_obj)
            self.assertEqual(raw_message, json.dumps(notification).encode())
        _handler.call_count = 0
        click_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, "verify_event_message") as verify:
            verify.return_value = True
            response = self.client.post(reverse("event_webhook"), json.dumps(notification), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)

    def test_bad_json(self):
        """
        Test request with invalid JSON.
        """
        response = self.client.post(reverse("event_webhook"), "This is not JSON", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, "The request body could not be deserialized. Bad JSON.".encode())

    def test_bad_signature(self):
        """
        Test handling a click event request.
        """
        req_mail_obj, req_click_obj, notification = get_mock_click()

        # Mock the verification
        with mock.patch.object(ses_utils, "verify_event_message") as verify:
            verify.return_value = False
            response = self.client.post(reverse("event_webhook"), json.dumps(notification), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, "Signature verification failed.".encode())
