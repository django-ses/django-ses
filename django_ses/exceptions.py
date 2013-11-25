from boto.exception import BotoServerError


class BlacklistedAddressException(BotoServerError):
    """
    Subclass of BotoServerError that indicates that the message was blacklisted.

    This exception class can propagate special properties of BotoServerError,
    such as ``status`` and ``reason``, if it is constructed with an instance of
    BotoServerError as the ``original_exception`` argument.
    """
    def __init__(self, message, original_exception=None, *args):
        self.message = message

        body = None
        if original_exception:
            body = original_exception.body

        BotoServerError.__init__(self, status=400, reason='Bad Request', body=body, *args)

    def __repr__(self):
        return '%s: %s' % (self.__class__.__name__, self.message)

    def __str__(self):
        return self.__repr__()


def is_blacklist_exception(exc):
    r"""
    Determine whether a BotoServerError was raised because of a blacklisted email address.

    Blacklist error response.
    >>> exc = BotoServerError(400, 'Bad Request', '<ErrorResponse xmlns="http://ses.amazonaws.com/doc/2010-12-01/">\n  <Error>\n    <Type>Sender</Type>\n    <Code>MessageRejected</Code>\n    <Message>Address blacklisted.</Message>\n  </Error>\n  <RequestId>00db668c-f3ba-11e0-a7a6-8323bf5c7d5e</RequestId>\n</ErrorResponse>\n')
    >>> is_blacklist_exception(exc)
    True

    Address not verified response, not a blacklisted error.
    >>> exc = BotoServerError(400, 'Bad Request', '<ErrorResponse xmlns="http://ses.amazonaws.com/doc/2010-12-01/">\n  <Error>\n    <Type>Sender</Type>\n    <Code>MessageRejected</Code>\n    <Message>Email address is not verified.</Message>\n  </Error>\n  <RequestId>d903fc16-4ffa-11e0-ab8f-7de313811634</RequestId>\n</ErrorResponse>\n')
    >>> is_blacklist_exception(exc)
    False

    Unrelated exception type.
    >>> is_blacklist_exception(TypeError())
    False
    """
    if not isinstance(exc, BotoServerError):
        return False
    return '<Message>Address blacklisted.</Message>' in exc.body
