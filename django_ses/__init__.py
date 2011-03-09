from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

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
                message.extra_headers['status'] = 200
                message.extra_headers['message_id'] = response['SendRawEmailResponse']['SendRawEmailResult']['MessageId']
                message.extra_headers['request_id'] = response['SendRawEmailResponse']['ResponseMetadata']['RequestId']
                num_sent += 1
            except SESConnection.ResponseError, err:
                # Store failure information so you can post process it if required
                error_keys = ['status', 'reason', 'body', 'request_id', 'error_code', 'error_message']
                for key in error_keys:
                    message.extra_headers[key] = getattr(err, key, None)
                if not self.fail_silently:
                    raise

        if new_conn_created:
            self.close()

        return num_sent

