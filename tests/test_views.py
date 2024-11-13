import json
import weakref

try:
    from unittest import mock
except ImportError:
    import mock

import django
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from django_ses import settings
from django_ses import utils as ses_utils
from django_ses.inbound import BaseHandler
from django_ses.signals import (
    bounce_received,
    click_received,
    complaint_received,
    delivery_received,
    open_received,
    send_received,
)
from tests.mocks import (
    get_mock_bounce,
    get_mock_click,
    get_mock_complaint,
    get_mock_delivery,
    get_mock_open,
    get_mock_received_sns,
    get_mock_send,
)


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

    def test_handle_bounce_event(self):
        """
        Test handling a normal bounce request.
        """
        req_mail_obj, req_bounce_obj, notification = get_mock_bounce("eventType")

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

            response = self.client.post(reverse("django_ses_bounce"), json.dumps(notification),
                                        content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)

    def test_handle_bounce_notification(self):
        """
        Test handling a normal bounce request.
        """
        req_mail_obj, req_bounce_obj, notification = get_mock_bounce("notificationType")

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

            response = self.client.post(reverse("django_ses_bounce"), json.dumps(notification),
                                        content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)


# We're using a TransactionTestCase instead of a TestCase because we want to
# avoid using transactions. Calls to atomic() will disconnect the signal
# handlers, which is exactly what we're trying to test here.
class HandleBounceTestCaseWithBL(TransactionTestCase):
    def test_bounce_event_can_perform_blacklist(self):
        """
        Test if bounce events result in blacklisted emails (if the feature has
        been enabled)
        """

        settings.VERIFY_BOUNCE_SIGNATURES = False

        mail_obj, bounce_obj, notification = get_mock_bounce("eventType")

        # We can't use mock.patch("django_ses.signals.bounce_handler") here
        # because the signal gets registered way before this code is executed.
        # We would be late even if we tried to patch it in the setUp() method.
        # The only way is to patch the actual .receivers prop at "this" exact
        # moment.
        mock_func = mock.MagicMock()
        receiver = bounce_received.receivers[0]

        # Django<5 had only synchronous receivers, but >=5 can have asynchronous
        # ones as well. This caused the receivers structure to change:
        #
        # 4.2.16: https://github.com/django/django/blob/4.2.16/django/dispatch/dispatcher.py#L253
        # 5.0: https://github.com/django/django/blob/5.0/django/dispatch/dispatcher.py#L431
        #
        # We must account for that difference and prepare a tuple that will
        # match the expected signature.
        if django.VERSION[0] < 5:
            receiver = (receiver[0], weakref.ref(mock_func))
        else:
            receiver = (receiver[0], weakref.ref(mock_func), False)
        bounce_received.receivers[0] = receiver
        response = self.client.post(reverse("django_ses_bounce"), json.dumps(notification),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_func.call_count, 1)

    def test_complaint_event_can_perform_blacklist(self):
        """
        Test if complaint events result in blacklisted emails (if the feature
        has been enabled)
        """

        settings.VERIFY_BOUNCE_SIGNATURES = False

        mail_obj, complaint_obj, notification = get_mock_complaint("eventType")

        # We can't use mock.patch("django_ses.signals.complaint_handler") here
        # because the signal gets registered way before this code is executed.
        # We would be late even if we tried to patch it in the setUp() method.
        # The only way is to patch the actual .receivers prop at "this" exact
        # moment.
        mock_func = mock.MagicMock()
        receiver = complaint_received.receivers[0]

        # Django<5 had only synchronous receivers, but >=5 can have asynchronous
        # ones as well. This caused the receivers structure to change:
        #
        # 4.2.16: https://github.com/django/django/blob/4.2.16/django/dispatch/dispatcher.py#L253
        # 5.0: https://github.com/django/django/blob/5.0/django/dispatch/dispatcher.py#L431
        #
        # We must account for that difference and prepare a tuple that will
        # match the expected signature.
        if django.VERSION[0] < 5:
            receiver = (receiver[0], weakref.ref(mock_func))
        else:
            receiver = (receiver[0], weakref.ref(mock_func), False)

        complaint_received.receivers[0] = receiver
        response = self.client.post(reverse("django_ses_bounce"), json.dumps(notification),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_func.call_count, 1)


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
        req_mail_obj, req_bounce_obj, notification = get_mock_bounce("eventType")

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
            response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                        content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)


    def test_handle_bounce_notification(self):
        """
        Test handling a normal bounce request.
        """
        req_mail_obj, req_bounce_obj, notification = get_mock_bounce("notificationType")

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
            response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                        content_type="application/json")
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
            response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                        content_type="application/json")
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
            response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                        content_type="application/json")
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
            response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                        content_type="application/json")
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
            response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                        content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_handler.call_count, 1)

    def test_handle_received_event(self):
        """
        Test handling a received event request.
        """
        settings.AWS_SES_INBOUND_HANDLER = "global.DummyClass"

        req_mail_obj, req_content, req_receipt_obj, notification = get_mock_received_sns()

        class DummyClass(BaseHandler):
            def process(self):
                pass

            def handle(self):
                pass

        with mock.patch("importlib.import_module") as mock_import_module:
            mock_import_module.return_value = mock.MagicMock(DummyClass=DummyClass)

            with mock.patch.object(DummyClass, "handle") as mock_handle:

                # Mock the verification
                with mock.patch.object(ses_utils, "verify_event_message") as verify:
                    verify.return_value = True
                    response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                                content_type="application/json")
                self.assertEqual(response.status_code, 200)

                mock_handle.assert_called_once()

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
            response = self.client.post(reverse("event_webhook"), json.dumps(notification),
                                        content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, "Signature verification failed.".encode())
