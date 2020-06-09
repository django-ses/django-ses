# -*- coding: utf-8 -*-

import email
from unittest import mock

import boto3
from django.core.mail import send_mail, EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.utils.encoding import smart_str

import django_ses
from django_ses import settings

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


class SESConfigurationSetTester(object):

    def __init__(self, configuration_set):
        self.message = None
        self.dkim_domain = None
        self.dkim_key = None
        self.dkim_selector = None
        self.dkim_headers = ()
        self.configuration_set = configuration_set

    def __call__(self, message, dkim_domain=None, dkim_key=None,
                 dkim_selector=None, dkim_headers=()):
        self.message = message
        self.dkim_domain = dkim_domain
        self.dkim_key = dkim_key
        self.dkim_selector = dkim_selector
        self.dkim_headers = dkim_headers
        return self.configuration_set


class FakeSESConnection(object):
    """
    A fake SES connection for testing purposes.It behaves similarly
    to django's dummy backend
    (https://docs.djangoproject.com/en/dev/topics/email/#dummy-backend)

    Emails sent with send_raw_email is stored in ``outbox`` attribute
    which is a list of kwargs received by ``send_raw_email``.
    """
    outbox = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.connection = boto3.client(
            'ses',
            aws_access_key_id='ACCESS_KEY',
            aws_secret_access_key='SECRET_KEY',
        )

        self.outbox.append(kwargs)

    def send_raw_email(self, **kwargs):
        self.outbox.append(kwargs)
        return {
            'MessageId': 'fake_message_id',
            'ResponseMetadata': {
                'RequestId': 'fake_request_id',
            },
        }

    def send_mail(self, subject, body, from_email, recipient_list):
        with mock.patch('boto3.client', return_value=self.connection):
            with mock.patch.object(self.connection, 'send_raw_email', return_value=self.send_raw_email()):
                # todo not working because we dont call the actual function -> need to override inside send_raw_email
                send_mail(subject, body, from_email, recipient_list)
        self.outbox.append(EmailMultiAlternatives(subject, body, from_email, recipient_list))


class FakeSESBackend(django_ses.SESBackend):
    """
    A fake SES backend for testing purposes. It overrides the real SESBackend's
    get_rate_limit method so we can run tests without valid AWS credentials.
    """

    def get_rate_limit(self):
        return 10


class SESBackendBaseTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.fake_connection = FakeSESConnection()

        cls.connection = boto3.client(
            'ses',
            aws_access_key_id='ACCESS_KEY',
            aws_secret_access_key='SECRET_KEY',
        )

    def tearDown(self):
        # Empty outbox every time test finishes
        self.fake_connection.outbox = []


class SESBackendTest(SESBackendBaseTest):

    @staticmethod
    def _rfc2047_helper(value_to_encode):
        # references: https://docs.python.org/3/library/email.header.html, https://tools.ietf.org/html/rfc2047.html
        name, addr = email.utils.parseaddr(value_to_encode)
        name = email.header.Header(name).encode()
        return email.utils.formataddr((name, addr))

    def test_rfc2047_helper(self):
        # Ensures that the underlying email.header library code is encoding as expected, using known values
        unicode_from_addr = u'Unicode Name Österreich <from@example.com>'
        rfc2047_encoded_from_addr = '=?utf-8?b?VW5pY29kZSBOYW1lIMOzw7PDs8Ozw7PDsw==?= <from@example.com>'
        self.assertEqual(self._rfc2047_helper(unicode_from_addr), rfc2047_encoded_from_addr)

    def test_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = None

        unicode_from_addr = u'Unicode Name Österreich <from@example.com>'
        self.fake_connection.send_mail('subject', 'body', unicode_from_addr, ['to@example.com'])
        message = self.fake_connection.outbox.pop()
        mail = email.message_from_string(smart_str(message['raw_message']))
        self.assertTrue('X-SES-CONFIGURAITON-SET' not in mail.keys())
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], self._rfc2047_helper(unicode_from_addr))
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_configuration_set_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = 'test-set'
        self.fake_connection.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.fake_connection.outbox.pop()
        mail = email.message_from_string(smart_str(message['raw_message']))
        self.assertEqual(mail['X-SES-CONFIGURATION-SET'], 'test-set')
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], 'from@example.com')
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_configuration_set_callable_send_mail(self):
        config_set_callable = SESConfigurationSetTester('my-config-set')
        settings.AWS_SES_CONFIGURATION_SET = config_set_callable
        self.fake_connection.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.fake_connection.outbox.pop()
        mail = email.message_from_string(smart_str(message['raw_message']))
        # ensure we got the correct configuration message payload
        self.assertEqual(mail['X-SES-CONFIGURATION-SET'], 'my-config-set')
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], 'from@example.com')
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')
        # ensure we passed in the proper arguments to our callable
        self.assertEqual(config_set_callable.message.subject, 'subject')
        self.assertEqual(config_set_callable.dkim_domain, None)
        self.assertEqual(config_set_callable.dkim_key, None)
        self.assertEqual(config_set_callable.dkim_selector, 'ses')
        self.assertEqual(config_set_callable.dkim_headers, ('From', 'To', 'Cc', 'Subject'))

    def test_dkim_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = None
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
        self.fake_connection.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.fake_connection.outbox.pop()['raw_message']
        self.assertTrue(dkim.verify(message))
        self.assertFalse(dkim.verify(message + 'some additional text'))
        self.assertFalse(dkim.verify(
                            message.replace('from@example.com', 'from@spam.com')))

    def test_return_path(self):
        """
        Ensure that the 'source' argument sent into send_raw_email uses
        settings.AWS_SES_RETURN_PATH, defaults to from address.
        """
        settings.AWS_SES_RETURN_PATH = None
        self.fake_connection.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.fake_connection.outbox.pop()['source'], 'from@example.com')


class SESBackendTestReturn(SESBackendBaseTest):

    @override_settings(EMAIL_BACKEND='tests.test_backend.FakeSESBackend')
    def test_return_path(self):
        settings.AWS_SES_RETURN_PATH = "return@example.com"
        self.fake_connection.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.fake_connection.outbox.pop()
        self.assertEqual(message.from_email, 'return@example.com')
