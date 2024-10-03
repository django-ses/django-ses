# -*- coding: utf-8 -*-

import email

from django.conf import settings as django_settings
from django.core.mail import EmailMessage, send_mail
from django.test import TestCase
from django.utils.encoding import smart_str

import django_ses
from django_ses import models, settings

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
DKIM_PUBLIC_KEY = 'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALCKsjD8UUxBESo1OLN6gptp1lD0U85AgXGL571/SQ3k61KhAQ8hhL3lnfQKn/' \
                  'XCl2oCXscEwgJv43IUs+VETWECAwEAAQ=='


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


class FakeSESConnection:
    """
    A fake SES connection for testing purposes.It behaves similarly
    to django's dummy backend
    (https://docs.djangoproject.com/en/dev/topics/email/#dummy-backend)

    Emails sent with send_raw_email is stored in ``outbox`` attribute
    which is a list of kwargs received by ``send_raw_email``.
    """
    outbox = []

    """Override `SESConnection.__init__ to skip session creation."""
    def __init__(self, *args, **kwargs):
        pass

    def send_raw_email(self, **kwargs):
        self.outbox.append(kwargs)
        return {
            'MessageId': 'fake_message_id',
            'ResponseMetadata': {
                'RequestId': 'fake_request_id',
                },
            }

    def send_email(self, **kwargs):
        self.outbox.append(kwargs)
        return {
            'MessageId': 'fake_message_id',
            'ResponseMetadata': {
                'RequestId': 'fake_request_id',
                },
            }

    @classmethod
    def client(cls, *args, **kwargs):
        return cls(args, kwargs)


class FakeSESBackend(django_ses.SESBackend):
    """
    A fake SES backend for testing purposes. It overrides the real SESBackend's
    get_rate_limit method so we can run tests without valid AWS credentials.
    """

    def get_rate_limit(self):
        return 10

    def create_session(self) -> FakeSESConnection:
        return FakeSESConnection


class SESBackendTest(TestCase):
    def setUp(self):
        # TODO: Fix this -- this is going to cause side effects
        django_settings.EMAIL_BACKEND = "tests.test_backend.FakeSESBackend"
        self.outbox = FakeSESConnection.outbox

    def tearDown(self):
        # Empty outbox every time test finishes
        FakeSESConnection.outbox = []

    def _rfc2047_helper(self, value_to_encode):
        # references: https://docs.python.org/3/library/email.header.html, https://tools.ietf.org/html/rfc2047.html
        name, addr = email.utils.parseaddr(value_to_encode)
        name = email.header.Header(name).encode()
        return email.utils.formataddr((name, addr))

    def test_rfc2047_helper(self):
        # Ensures that the underlying email.header library code is encoding as expected, using known values
        unicode_from_addr = 'Unicode Name óóóóóó <from@example.com>'
        rfc2047_encoded_from_addr = '=?utf-8?b?VW5pY29kZSBOYW1lIMOzw7PDs8Ozw7PDsw==?= <from@example.com>'
        self.assertEqual(self._rfc2047_helper(unicode_from_addr), rfc2047_encoded_from_addr)

    def test_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = None

        from_addr = 'Albertus Magnus <albertus.magnus@example.com>'

        send_mail('subject', 'body', from_addr, ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['RawMessage']['Data']))
        self.assertTrue('X-SES-CONFIGURATION-SET' not in mail.keys())
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], self._rfc2047_helper(from_addr))
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_send_mail_when_blacklisted(self):
        settings.AWS_SES_USE_BLACKLIST = True

        len_queue = len(self.outbox)
        send_mail('Hello', 'world', 'foo@bar.com', ['xyz@bar.com'])
        # It should have sent the email because 'xyz@bar.com' is not blacklisted
        self.assertEqual(len_queue + 1, len(self.outbox))

        models.BlacklistedEmail.objects.create(email='xyz@bar.com')

        len_queue = len(self.outbox)
        send_mail('Hello', 'world', 'foo@bar.com', ['xyz@bar.com'])
        # It shouldn't have sent the email because 'xyz@bar.com' is blacklisted
        self.assertEqual(len_queue, len(self.outbox))

        settings.AWS_SES_USE_BLACKLIST = False
        len_queue = len(self.outbox)
        send_mail('Hello', 'world', 'foo@bar.com', ['xyz@bar.com'])
        # It should have sent the email because even if 'xyz@bar.com' is
        # blacklisted, AWS_SES_USE_BLACKLIST is set to False
        self.assertEqual(len_queue + 1, len(self.outbox))

    def test_send_mail_to_cc_bcc_when_blacklisted(self):
        settings.AWS_SES_USE_BLACKLIST = True
        models.BlacklistedEmail.objects.create(email='foo1@bar.com')
        models.BlacklistedEmail.objects.create(email='foo2@bar.com')

        len_queue = len(self.outbox)
        email = EmailMessage(
            subject='Hello',
            body='world',
            from_email='from@email.com',
            to=['foo@bar.com'],
            bcc=['foo1@bar.com', 'foo3@bar.com'],
            cc=['foo2@bar.com', 'foo4@bar.com']
        )
        email.send()

        self.assertEqual(len_queue + 1, len(self.outbox))
        destinations = self.outbox[0].get('Destinations')
        self.assertEqual(len(destinations), 3)
        self.assertIn('foo@bar.com', destinations)
        self.assertIn('foo3@bar.com', destinations)
        self.assertIn('foo4@bar.com', destinations)

    def test_send_mail_unicode_body(self):
        settings.AWS_SES_CONFIGURATION_SET = None

        unicode_from_addr = 'Unicode Name óóóóóó <from@example.com>'

        send_mail('Scandinavian', 'Sören & Björn', unicode_from_addr, ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['RawMessage']['Data']))
        self.assertTrue('X-SES-CONFIGURATION-SET' not in mail.keys())
        self.assertEqual(mail['subject'], 'Scandinavian')
        self.assertEqual(mail['from'], self._rfc2047_helper(unicode_from_addr))
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'Sören & Björn')

    def test_configuration_set_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = 'test-set'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['RawMessage']['Data']))
        self.assertEqual(mail['X-SES-CONFIGURATION-SET'], 'test-set')
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], 'from@example.com')
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_configuration_set_callable_send_mail(self):
        config_set_callable = SESConfigurationSetTester('my-config-set')
        settings.AWS_SES_CONFIGURATION_SET = config_set_callable
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['RawMessage']['Data']))
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


class SESV2BackendTest(TestCase):
    def setUp(self):
        django_settings.EMAIL_BACKEND = 'tests.test_backend.FakeSESBackend'
        settings.USE_SES_V2 = True
        settings.AWS_SES_FROM_ARN = None
        settings.AWS_SES_SOURCE_ARN = None
        self.outbox = FakeSESConnection.outbox

    def tearDown(self):
        # Empty outbox every time test finishes
        settings.USE_SES_V2 = False
        FakeSESConnection.outbox = []

    def _rfc2047_helper(self, value_to_encode):
        # references: https://docs.python.org/3/library/email.header.html, https://tools.ietf.org/html/rfc2047.html
        name, addr = email.utils.parseaddr(value_to_encode)
        name = email.header.Header(name).encode()
        return email.utils.formataddr((name, addr))

    def test_rfc2047_helper(self):
        # Ensures that the underlying email.header library code is encoding as expected, using known values
        unicode_from_addr = 'Unicode Name óóóóóó <from@example.com>'
        rfc2047_encoded_from_addr = '=?utf-8?b?VW5pY29kZSBOYW1lIMOzw7PDs8Ozw7PDsw==?= <from@example.com>'
        self.assertEqual(self._rfc2047_helper(unicode_from_addr), rfc2047_encoded_from_addr)

    def test_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = None

        unicode_from_addr = 'Unicode Name óóóóóó <from@example.com>'

        send_mail('subject', 'body', unicode_from_addr, ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['Content']['Raw']['Data']))
        self.assertTrue('X-SES-CONFIGURATION-SET' not in mail.keys())
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], self._rfc2047_helper(unicode_from_addr))
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_configuration_set_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = 'test-set'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['Content']['Raw']['Data']))
        self.assertEqual(mail['X-SES-CONFIGURATION-SET'], 'test-set')
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], 'from@example.com')
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_configuration_set_callable_send_mail(self):
        config_set_callable = SESConfigurationSetTester('my-config-set')
        settings.AWS_SES_CONFIGURATION_SET = config_set_callable
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['Content']['Raw']['Data']))
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
                'id 1\n;ANSWER\n%s 60 IN TXT "v=DKIM1; p=%s"' %
                (qname, DKIM_PUBLIC_KEY))
            return dns.resolver.Answer(name, rdtype, 1, response)

        dns.resolver.query = dns_query

        settings.DKIM_DOMAIN = 'example.com'
        settings.DKIM_PRIVATE_KEY = DKIM_PRIVATE_KEY
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()['RawMessage']
        self.assertTrue(dkim.verify(message))
        self.assertFalse(dkim.verify(message + 'some additional text'))
        self.assertFalse(dkim.verify(
                            message.replace('from@example.com', 'from@spam.com')))

    def test_return_path(self):
        """Ensure that the 'Source' argument sent into send_raw_email uses FromEmailAddress.
        """
        settings.AWS_SES_RETURN_PATH = None
        settings.AWS_SES_FROM_EMAIL = 'from@example.com'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['FromEmailAddress'], 'from@example.com')

    def test_feedback_forwarding(self):
        """
        Ensure that the notification address argument uses FeedbackForwardingEmailAddress.
        """
        settings.AWS_SES_RETURN_PATH = 'reply@example.com'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['FeedbackForwardingEmailAddress'], 'reply@example.com')

    def test_source_arn_is_not_set(self):
        """
        Ensure that the helpers for Identity Owner for SES Sending Authorization are not present, if nothing has been
        configured.
        """
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        mail = self.outbox.pop()
        self.assertNotIn('FromEmailAddressIdentityArn', mail)

    def test_source_arn_is_set(self):
        """
        Ensure that the helpers for Identity Owner for SES Sending Authorization are set correctly.
        """
        settings.AWS_SES_SOURCE_ARN = 'arn:aws:ses:eu-central-1:111111111111:identity/example.com'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        mail = self.outbox.pop()
        self.assertEqual(mail['FromEmailAddressIdentityArn'],
                         'arn:aws:ses:eu-central-1:111111111111:identity/example.com')

    def test_from_arn_takes_precedence_when_source_arn_is_set(self):
        """
        Ensure that the helpers for Identity Owner for SES Sending Authorization are set correctly.
        """
        settings.AWS_SES_SOURCE_ARN = 'arn:aws:ses:eu-central-1:111111111111:identity/example.com'
        settings.AWS_SES_FROM_ARN = 'arn:aws:ses:eu-central-1:222222222222:identity/example.com'
        settings.AWS_SES_RETURN_PATH_ARN = 'arn:aws:ses:eu-central-1:333333333333:identity/example.com'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        mail = self.outbox.pop()
        self.assertEqual(mail['FromEmailAddressIdentityArn'],
                         'arn:aws:ses:eu-central-1:222222222222:identity/example.com')


class SESBackendTestInitialize(TestCase):
    def test_auto_throttle(self):
        """
        Ensure that SESBackend handles aws_auto_throttle correctly
        """
        for throttle_param, throttle_setting, expected_throttle_val in (
            # If provided, we should cast parameter to float
            (1.0, 2.0, 1.0),
            ("1.0", 2.0, 1.0),

            # On 0 or None, we should fall back to the value in Django settings,
            # casting that value to a float
            (0, 2.0, 2.0),
            (None, 2.0, 2.0),
            (None, "1.0", 1.0),
            (None, None, None),
        ):
            settings.AWS_SES_AUTO_THROTTLE = throttle_setting
            backend = django_ses.SESBackend(aws_auto_throttle=throttle_param)
            self.assertEqual(backend._throttle, expected_throttle_val)


class SESBackendTestReturn(TestCase):
    def setUp(self):
        # TODO: Fix this -- this is going to cause side effects
        django_settings.EMAIL_BACKEND = 'tests.test_backend.FakeSESBackend'
        django_ses.SESConnection = FakeSESConnection
        self.outbox = FakeSESConnection.outbox

    def tearDown(self):
        # Empty outbox everytime test finishes
        FakeSESConnection.outbox = []

    def test_from_email(self):
        settings.AWS_SES_FROM_EMAIL = "my_default_from@example.com"
        send_mail('subject', 'body', 'ignored_from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['Source'], 'my_default_from@example.com')

    def test_return_path(self):
        settings.USE_SES_V2 = True
        settings.AWS_SES_RETURN_PATH = "return@example.com"
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()

        self.assertEqual(message['FromEmailAddress'], 'my_default_from@example.com')
        self.assertEqual(message['FeedbackForwardingEmailAddress'], 'return@example.com')
