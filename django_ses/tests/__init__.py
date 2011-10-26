from collections import defaultdict
from boto.exception import BotoServerError

def enable_fake_ses_connection():
    # Switch out the boto SESConnection that is used by django_ses with a fake
    # one that records calls to important methods.
    class FakeSESConnection(object):
        # Information for assertions in tests.
        function_calls = defaultdict(list)
        blacklist = []

        DefaultHost = 'fake_email_host'
        ResponseError = BotoServerError

        def __init__(self, *args, **kwargs):
            pass

        def send_raw_email(self, *args, **kwargs):
            FakeSESConnection.function_calls['send_raw_email'].append((args, kwargs))

            destinations = kwargs.get('destinations', [])

            if any(d in FakeSESConnection.blacklist for d in destinations):
                raise BotoServerError(
                    400,
                    'Bad Request',
                    ('<ErrorResponse xmlns="http://ses.amazonaws.com/doc/2010-12-01/">\n'
                     '    <Error>\n'
                     '        <Type>Sender</Type>\n'
                     '            <Code>MessageRejected</Code>\n'
                     '        <Message>Address blacklisted.</Message>\n'
                     '    </Error>\n'
                     '    <RequestId>00db668c-f3ba-11e0-a7a6-8323bf5c7d5e</RequestId>\n'
                     '</ErrorResponse>\n'),
                )

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

    # Monkeypatch the django_ses module to use the fake connection.
    import django_ses
    django_ses.SESConnection = FakeSESConnection

    # Return the fake connection so we can use it in the test.
    return FakeSESConnection
