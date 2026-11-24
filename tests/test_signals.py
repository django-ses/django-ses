from unittest import mock

from django.core.mail import send_mail
from django.db import NotSupportedError
from django.test import TestCase, override_settings

from django_ses import models, signals
from tests.mocks import (
    get_mock_bounce,
    get_mock_bounce_no_status,
    get_mock_bounce_no_status_transient,
    get_mock_bounce_transient_with_status,
    get_mock_complaint,
)


class SignalsTestCase(TestCase):
    """
    Test the signals handlers.
    """

    def test_bounce_handler(self):
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        mail_obj, bounce_obj, notification = get_mock_bounce("eventType")

        # It shouldn't insert the email in the blacklist if the feature hasn't
        # been enabled
        signals.bounce_handler(None, mail_obj, bounce_obj, notification)
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        # ... but after enabling the feature...
        with override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True):
            signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        # ... it should insert the email in the blacklist
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 1)

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_twice(self):
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        mail_obj, bounce_obj, notification = get_mock_bounce("eventType")

        # ... it should insert the email in the blacklist
        signals.bounce_handler(None, mail_obj, bounce_obj, notification)
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 1)

        # ... it shouldn't insert the email in the blacklist again
        signals.bounce_handler(None, mail_obj, bounce_obj, notification)
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 1)

    def test_bounce_handler_no_status(self):
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        mail_obj, bounce_obj, notification = get_mock_bounce_no_status("eventType")

        with override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True):
            signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 2)

    def test_bounce_handler_no_status_transient(self):
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        mail_obj, bounce_obj, notification = get_mock_bounce_no_status_transient("eventType")

        with override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True):
            signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        # ... it should not insert the email in the blacklist
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_transient_with_5xx_status(self):
        # SES reports a full mailbox as a Transient bounce with a 5.2.2 status:
        # the address can receive email again, so it must not be blacklisted.
        mail_obj, bounce_obj, notification = get_mock_bounce_transient_with_status("eventType")

        signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        self.assertEqual(models.BlacklistedEmail.objects.count(), 0)

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_undetermined_with_5xx_status(self):
        mail_obj, bounce_obj, notification = get_mock_bounce_transient_with_status(
            "eventType", bounce_type="Undetermined", bounce_sub_type="Undetermined"
        )

        signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        self.assertEqual(models.BlacklistedEmail.objects.count(), 0)

    def test_complaint_handler(self):
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        mail_obj, complaint_obj, notification = get_mock_complaint("eventType")

        # It shouldn't insert the email in the blacklist if the feature hasn't
        # been enabled
        signals.complaint_handler(None, mail_obj, complaint_obj, notification)
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        # ... but after enabling the feature...
        with override_settings(AWS_SES_ADD_COMPLAINT_TO_BLACKLIST=True):
            signals.complaint_handler(None, mail_obj, complaint_obj, notification)

        # ... it should insert the email in the blacklist
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 1)

    @override_settings(AWS_SES_ADD_COMPLAINT_TO_BLACKLIST=True)
    def test_complaint_handler_twice(self):
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 0)

        mail_obj, complaint_obj, notification = get_mock_complaint("eventType")

        # ... it should insert the email in the blacklist
        signals.complaint_handler(None, mail_obj, complaint_obj, notification)
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 1)

        # ... it shouldn't insert the email in the blacklist again
        signals.complaint_handler(None, mail_obj, complaint_obj, notification)
        count = models.BlacklistedEmail.objects.all().count()
        self.assertEqual(count, 1)

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_stores_reason(self):
        mail_obj, bounce_obj, notification = get_mock_bounce("eventType")

        signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        blacklisted = models.BlacklistedEmail.objects.get()
        self.assertEqual(blacklisted.email, "recipient1@example.com")
        self.assertEqual(
            blacklisted.reason,
            "Bounce\n"
            "Bounce type: Permanent\n"
            "Bounce sub-type: General\n"
            "Status: 5.0.0\n"
            "Action: failed\n"
            "Diagnostic code: smtp; 550 user unknown\n"
            "Reporting MTA: example.com\n"
            "Timestamp: 2012-05-25T14:59:38.605-07:00\n"
            "Feedback ID: 000001378603176d-5a4b5ad9-6f30-4198-a8c3-b1eb0c270a1d-000000",
        )

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_stores_reason_for_many_recipients(self):
        mail_obj, bounce_obj, notification = get_mock_bounce_no_status("eventType")

        signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        reasons = dict(models.BlacklistedEmail.objects.values_list("email", "reason"))
        self.assertEqual(set(reasons), {"recipient1@example.com", "recipient2@example.com"})
        for reason in reasons.values():
            self.assertTrue(reason.startswith("Bounce\nBounce type: Permanent\nBounce sub-type: General\n"))
            # These recipients have no status, action or diagnostic code, so those lines are left out.
            self.assertNotIn("Status:", reason)
            self.assertNotIn("Diagnostic code:", reason)

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_keeps_existing_reason(self):
        models.BlacklistedEmail.objects.create(email="recipient1@example.com", reason="Added by hand")
        mail_obj, bounce_obj, notification = get_mock_bounce("eventType")

        signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        self.assertEqual(models.BlacklistedEmail.objects.get().reason, "Added by hand")

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_fills_blank_reason(self):
        # A row blacklisted before the reason field existed has a blank reason.
        models.BlacklistedEmail.objects.create(email="recipient1@example.com")
        mail_obj, bounce_obj, notification = get_mock_bounce("eventType")

        signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        blacklisted = models.BlacklistedEmail.objects.get()
        self.assertTrue(blacklisted.reason.startswith("Bounce\nBounce type: Permanent\n"))
        self.assertIn("Diagnostic code: smtp; 550 user unknown", blacklisted.reason)

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_fills_blank_reason_for_many_recipients(self):
        models.BlacklistedEmail.objects.create(email="recipient1@example.com")
        models.BlacklistedEmail.objects.create(email="recipient2@example.com", reason="Added by hand")
        mail_obj, bounce_obj, notification = get_mock_bounce_no_status("eventType")

        signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        reasons = dict(models.BlacklistedEmail.objects.values_list("email", "reason"))
        self.assertTrue(reasons["recipient1@example.com"].startswith("Bounce\nBounce type: Permanent\n"))
        self.assertEqual(reasons["recipient2@example.com"], "Added by hand")

    @override_settings(AWS_SES_ADD_BOUNCE_TO_BLACKLIST=True)
    def test_bounce_handler_without_ignore_conflicts(self):
        # Oracle doesn't support ignore_conflicts, so each email is blacklisted one by one.
        models.BlacklistedEmail.objects.create(email="recipient1@example.com")
        models.BlacklistedEmail.objects.create(email="recipient2@example.com", reason="Added by hand")
        mail_obj, bounce_obj, notification = get_mock_bounce_no_status("eventType")

        with mock.patch("django.db.models.query.QuerySet.bulk_create", side_effect=NotSupportedError):
            signals.bounce_handler(None, mail_obj, bounce_obj, notification)

        reasons = dict(models.BlacklistedEmail.objects.values_list("email", "reason"))
        self.assertTrue(reasons["recipient1@example.com"].startswith("Bounce\nBounce type: Permanent\n"))
        self.assertEqual(reasons["recipient2@example.com"], "Added by hand")

    @override_settings(AWS_SES_ADD_COMPLAINT_TO_BLACKLIST=True)
    def test_complaint_handler_fills_blank_reason(self):
        models.BlacklistedEmail.objects.create(email="recipient1@example.com")
        mail_obj, complaint_obj, notification = get_mock_complaint("eventType")

        signals.complaint_handler(None, mail_obj, complaint_obj, notification)

        self.assertTrue(models.BlacklistedEmail.objects.get().reason.startswith("Complaint\n"))

    @override_settings(AWS_SES_ADD_COMPLAINT_TO_BLACKLIST=True)
    def test_complaint_handler_stores_reason(self):
        mail_obj, complaint_obj, notification = get_mock_complaint("eventType")

        signals.complaint_handler(None, mail_obj, complaint_obj, notification)

        blacklisted = models.BlacklistedEmail.objects.get()
        self.assertEqual(blacklisted.email, "recipient1@example.com")
        self.assertEqual(
            blacklisted.reason,
            "Complaint\n"
            "Complaint feedback type: abuse\n"
            "User agent: ExampleCorp Feedback Loop (V0.01)\n"
            "Timestamp: 2012-05-25T14:59:38.623Z\n"
            "Feedback ID: 000001378603177f-18c07c78-fa81-4a58-9dd1-fedc3cb8f49a-000000",
        )

    @override_settings(EMAIL_BACKEND="tests.test_backend.FakeSESBackend")
    def test_message_sent_handler(self):
        def _handler(sender, message, **kwargs):
            _handler.call_count += 1
            self.assertEqual(message.subject, "subject")
            self.assertEqual(message.body, "body")
            self.assertEqual(message.extra_headers["message_id"], "fake_message_id")

        _handler.call_count = 0
        signals.message_sent.connect(_handler)

        send_mail("subject", "body", "from@example.com", ["to@example.com"])
        self.assertEqual(_handler.call_count, 1)
