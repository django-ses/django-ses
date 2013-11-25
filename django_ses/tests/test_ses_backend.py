from django.test import TestCase
from django.conf import settings
from django.core import mail

from django_ses.tests import enable_fake_ses_connection
from django_ses.exceptions import BlacklistedAddressException


class SESBackendTestCase(TestCase):
    def setUp(self):
        settings.EMAIL_BACKEND = 'django_ses.SESBackend'

    def test_send_mail(self):
        # Send a test email, and ensure that the calls passed along to boto are correct.
        fake_conn = enable_fake_ses_connection()

        mail.send_mail(
            'fake_subject',
            'fake_body',
            'from@example.com',
            ['to@example.com'],
            fail_silently=False,
        )

        # Check that boto.SESConnection.send_raw_email was called correctly.
        calls = fake_conn.function_calls['send_raw_email']
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]

        self.assertEqual(args, ())
        self.assertEqual(kwargs['source'], 'from@example.com')
        self.assertEqual(kwargs['destinations'], ['to@example.com'])

        raw_message = kwargs['raw_message']
        assert raw_message.startswith(
            'Content-Type: text/plain; charset="utf-8"\n'
            'MIME-Version: 1.0\n'
            'Content-Transfer-Encoding: quoted-printable\n'
            'Subject: fake_subject\n'
            'From: from@example.com\n'
            'To: to@example.com\n'
        )
        assert raw_message.endswith('\nfake_body')

    def test_send_mail_blacklisted(self):
        # Send a test email to a mocked blacklisted address, and ensure that it
        # raises a useful exception.
        fake_conn = enable_fake_ses_connection()
        fake_conn.blacklist.append('blacklisted@example.com')

        self.assertRaises(
            BlacklistedAddressException,
            lambda: mail.send_mail(
                'fake_subject',
                'fake_body',
                'from@example.com',
                ['blacklisted@example.com'],
                fail_silently=False,
            )
        )

        # Check that boto.SESConnection.send_raw_email was called correctly.
        calls = fake_conn.function_calls['send_raw_email']
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]

        self.assertEqual(args, ())
        self.assertEqual(kwargs['source'], 'from@example.com')
        self.assertEqual(kwargs['destinations'], ['blacklisted@example.com'])

        raw_message = kwargs['raw_message']
        assert raw_message.startswith(
            'Content-Type: text/plain; charset="utf-8"\n'
            'MIME-Version: 1.0\n'
            'Content-Transfer-Encoding: quoted-printable\n'
            'Subject: fake_subject\n'
            'From: from@example.com\n'
            'To: blacklisted@example.com\n'
        )
        assert raw_message.endswith('\nfake_body')
