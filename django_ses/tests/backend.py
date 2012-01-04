import email

from django.conf import settings
from django.core.mail import send_mail
from django.test import TestCase

import django_ses
from boto.ses import SESConnection


class FakeSESConnection(SESConnection):
    '''
    A fake SES connection for testing purposes.It behaves similarly
    to django's dummy backend
    (https://docs.djangoproject.com/en/dev/topics/email/#dummy-backend)

    Emails sent with send_raw_email is stored in ``outbox`` attribute
    which is a list of kwargs received by ``send_raw_email``.
    '''
    outbox = []

    def __init__(self, *args, **kwargs):
        pass

    def send_raw_email(self, **kwargs):
        self.outbox.append(kwargs)
        response = {
            'SendRawEmailResponse': {
                'SendRawEmailResult': {
                    'MessageId': 'fake_message_id',
                },
                'ResponseMetadata': {
                    'RequestId': 'fake_request_id',
                },
            }
        }
        return response


class FakeSESBackend(django_ses.SESBackend):
    '''
    A fake SES backend for testing purposes. It overrides the real SESBackend's
    get_rate_limit method so we can run tests without valid AWS credentials.
    '''

    def get_rate_limit(self):
        return 10


class SESBackendTest(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = 'django_ses.tests.backend.FakeSESBackend'
        django_ses.SESConnection = FakeSESConnection
        self.outbox = FakeSESConnection.outbox

    def tearDown(self):
        # Empty outbox everytime test finishes
        FakeSESConnection.outbox = []

    def test_send_mail(self):
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(message['raw_message'])
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], 'from@example.com')
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_return_path(self):
        '''
        Ensure that the 'source' argument sent into send_raw_email uses
        settings.AWS_SES_RETURN_PATH, defaults to from address.
        '''
        settings.AWS_SES_RETURN_PATH = None
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['source'], 'from@example.com')

        settings.AWS_SES_RETURN_PATH = 'return@example.com'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['source'], 'return@example.com')
