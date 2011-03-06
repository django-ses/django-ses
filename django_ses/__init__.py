from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

import threading

from boto.ses import SESConnection


__version__ = '0.1'
__author__ = 'Harry Marr'


class SESBackend(BaseEmailBackend):
    """A Django Email backend that uses Amazon's Simple Email Service.
    """

    def __init__(self, fail_silently=False, *args, **kwargs):
        super(SESBackend, self).__init__(fail_silently=fail_silently, *args,
                                         **kwargs)

        self._access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        self._access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        self._api_endpoint = getattr(settings, 'AWS_SES_API_HOST',
                                     SESConnection.DefaultHost)

        self.connection = None

    def open(self):
        """Create a connection to the AWS API server. This can be reused for
        sending multiple emails.
        """
        if self.connection:
            return False

        try:
            self.connection = SESConnection(
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._access_key,
                host=self._api_endpoint,
            )
        except:
            if not self.fail_silently:
                raise

    def close(self):
        """Close any open HTTP connections to the API server.
        """
        try:
            self.connection.close()
            self.connection = None
        except:
            if not self.fail_silently:
                raise

    def send_messages(self, email_messages):
        """Sends one or more EmailMessage objects and returns the number of
        email messages sent.
        """
        if not email_messages:
            return

        new_conn_created = self.open()
        if not self.connection:
            # Failed silently
            return

        num_sent = 0
        for message in email_messages:
            try:
                response = self.connection.send_raw_email(
                    source=message.from_email,
                    destinations=message.recipients(),
                    raw_message=message.message().as_string(),
                )
                send_response = response['SendRawEmailResponse']
                send_result = send_response['SendRawEmailResult']
                message.extra_headers['Message-Id'] = send_result['MessageId']

                num_sent += 1
            except SESConnection.ResponseError:
                if not self.fail_silently:
                    raise
                pass

        if new_conn_created:
            self.close()

        return num_sent

