from collections import defaultdict
from boto.exception import BotoServerError

def enable_fake_ses_connection():
    # Switch out the boto SESConnection that is used by django_ses with a fake
    # one that records calls to important methods.
    class FakeSESConnection(object):
        function_calls = defaultdict(list)

        DefaultHost = 'fake_email_host'
        ResponseError = BotoServerError

        def __init__(self, *args, **kwargs):
            pass

        def send_raw_email(self, *args, **kwargs):
            FakeSESConnection.function_calls['send_raw_email'].append((args, kwargs))
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
