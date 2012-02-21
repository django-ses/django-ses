import email

from django.conf import settings as django_settings
from django.core.mail import send_mail
from django.test import TestCase

from boto.ses import SESConnection

import django_ses
from django_ses import settings
from django_ses.tests.utils import unload_django_ses

# random key generated with `openssl genrsa 512`
DKIM_PRIVATE_KEY = '''
-----BEGIN RSA PRIVATE KEY-----
MIIBOwIBAAJBALCKsjD8UUxBESo1OLN6gptp1lD0U85AgXGL571/SQ3k61KhAQ8h
hL3lnfQKn/XCl2oCXscEwgJv43IUs+VETWECAwEAAQJAQ8XK6GFEuHhWJZTu4n/K
ee0keEmDjq9WwgdKfIXLvsgaaNxCObhzv7G5rPU+U/3z1/0CtGR+DOPgoiaI/5HM
XQIhAN4h+o2WzRrz+dD/+zMGC9h1KEFvukIoP62kLOxW0eg/AiEAy3VD+UkRni4H
6UEJgCe0oZIiBCxj12/wUHFj1cfJYl8CICsndsGjFl2yIEpWMLsM5ag7uoJb7leD
8jsNthyEEWuJAiEAjeF6w26HEK286pZmD66gskN74TkrbuMqzI4mNsCZ2TUCIQCJ
HuuR7wc0HJ/cfVi8Kgm5B+sHY9/7KDWAYGGnbGgCNA==
-----END RSA PRIVATE KEY-----
'''
DKIM_PUBLIC_KEY = 'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALCKsjD8UUxBESo1OLN6gptp1lD0U85AgXGL571/SQ3k61KhAQ8hhL3lnfQKn/XCl2oCXscEwgJv43IUs+VETWECAwEAAQ=='


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
        # TODO: Fix this -- this is going to cause side effects
        django_settings.EMAIL_BACKEND = 'django_ses.tests.backend.FakeSESBackend'
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

    def test_dkim_mail(self):
        # DKIM verification uses DNS to retrieve the public key when checking
        # the signature, so we need to replace the standard query response with
        # one that always returns the test key.
        try:
            import dkim
            import dns
        except ImportError:
            return

        def dns_query(qname, rdtype):
            name = dns.name.from_text(qname)
            response = dns.message.from_text(
                    'id 1\n;ANSWER\n%s 60 IN TXT "v=DKIM1; p=%s"' %\
                            (qname, DKIM_PUBLIC_KEY))
            return dns.resolver.Answer(name, rdtype, 1, response)
        dns.resolver.query = dns_query

        settings.DKIM_DOMAIN = 'example.com'
        settings.DKIM_PRIVATE_KEY = DKIM_PRIVATE_KEY
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()['raw_message']
        self.assertTrue(dkim.verify(message))
        self.assertFalse(dkim.verify(message + 'some additional text'))
        self.assertFalse(dkim.verify(
                            message.replace('from@example.com', 'from@spam.com')))

    def test_return_path(self):
        '''
        Ensure that the 'source' argument sent into send_raw_email uses
        settings.AWS_SES_RETURN_PATH, defaults to from address.
        '''
        settings.AWS_SES_RETURN_PATH = None
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['source'], 'from@example.com')


class SESBackendTestReturn(TestCase):
    def setUp(self):
        # TODO: Fix this -- this is going to cause side effects
        django_settings.EMAIL_BACKEND = 'django_ses.tests.backend.FakeSESBackend'
        django_ses.SESConnection = FakeSESConnection
        self.outbox = FakeSESConnection.outbox

    def tearDown(self):
        # Empty outbox everytime test finishes
        FakeSESConnection.outbox = []

    def test_return_path(self):
        settings.AWS_SES_RETURN_PATH = "return@example.com"
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['source'], 'return@example.com')
