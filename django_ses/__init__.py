from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

import threading

from boto.ses import SESConnection


__version__ = '0.1'
__author__ = 'Harry Marr'

from smtplib import (
    SMTPSenderRefused,
    SMTPAuthenticationError,
)
from socket import error as socket_error

# Map of error codes to their smtplib equivelant. Eases integration of the SES
# backend with libraries like django-mailer who expect smtp-based errors.
# For exceptions that don't match cleanly to a smtplib equivelant, the original
# exception is raised (None)
# http://docs.amazonwebservices.com/ses/latest/APIReference/CommonErrors.html
SMTP_ERROR_MAP = {
    400: {
        'IncompleteSignature': SMTPSenderRefused,
        'InvalidAction': None,
        'InvalidParameterCombination': None,
        'InvalidParemeterValue': None,
        'InvalidQueryParameter': None,
        'MissingAction': None,
        'MessageRejected': SMTPAuthenticationError,
        'MissingParameter': None,
        'RequestExpired': socket_error,
        'Throttling': SMTPSenderRefused,
    },
    403: {
        'InvalidClientTokenId': SMTPAuthenticationError,
        'MissingAuthenticationToken': SMTPAuthenticationError,
        'OptInRequired': SMTPAuthenticationError,
    },
    404: {
        'MalformedQueryString': None,
    },
    500: {
        'InternalFailure': socket_error,
    },
    503: {
        'ServiceUnavailable': socket_error,
    },
}

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
        self._lock = threading.RLock()

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

    def _wrap_response_error(self, response_error):
        """
        Wraps SES errors in smtplib equivalants, if available.
        ''response_error'' A boto.exception.BotoServerError with an SES error.
        """
        status_dict = SMTP_ERROR_MAP.get(response_error.status, None)
        if status_dict:
            mapped_error = status_dict.get(response_error.error_code, None)
            if mapped_error:
                raise mapped_error(response_error.status, str(response_error))

        # No mapped error, raise the original exception
        raise

    def send_messages(self, email_messages):
        """Sends one or more EmailMessage objects and returns the number of
        email messages sent.
        """
        if not email_messages:
            return

        self._lock.acquire()
        try:
            new_conn_created = self.open()
            if not self.connection:
                # Failed silently
                return

            num_sent = 0
            for message in email_messages:
                try:
                    self.connection.send_raw_email(
                        source=message.from_email,
                        destinations=message.recipients(),
                        raw_message=message.message().as_string(),
                    )
                    num_sent += 1
                except SESConnection.ResponseError, err:
                    if not self.fail_silently:
                        self._wrap_response_error(err)
                    pass

            if new_conn_created:
                self.close()

        finally:
            self._lock.release()
        return num_sent

