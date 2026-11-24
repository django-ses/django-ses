import base64
import logging
import re
import warnings
from builtins import bytes
from email.utils import parseaddr
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from django.core.exceptions import ImproperlyConfigured
from django.db import NotSupportedError

from django_ses import settings
from django_ses.deprecation import RemovedInDjangoSES20Warning

logger = logging.getLogger(__name__)

_CERT_CACHE = {}

SES_REGEX_CERT_URL = re.compile(
    r"(?i)^https://sns\.[a-z0-9\-]+\.amazonaws\.com(\.cn)?/SimpleNotificationService\-[a-z0-9]+\.pem$"
)
SES_REGEX_SNS_ENDPOINT_HOST = re.compile(r"(?i)^sns\.[a-z0-9\-]+\.amazonaws\.com(\.cn)?$")


def clear_cert_cache():
    """Clear the certificate cache.

    This one-liner exists to discourage imports and direct usage of
    _CERT_CACHE.

    :returns None
    """
    _CERT_CACHE.clear()


class EventMessageVerifier(object):
    """
    A utility class for validating event messages

    See: http://docs.amazonwebservices.com/sns/latest/gsg/SendMessageToHttp.verify.signature.html
    """

    _REQ_DEP_TMPL = (
        "%s is required for event message verification. Please install "
        "`django-ses` with the `event` extra - e.g. "
        "`pip install django-ses[events]`."
    )

    def __init__(self, notification):
        """
        Creates a new event message from the given dict.
        """
        self._data = notification
        self._verified = None

    def is_verified(self):
        """
        Verifies an SES event message.

        Sign the bytes from the notification and compare it to the signature in
        the notification. If same, return True; else False.
        """
        if self._verified is not None:
            return self._verified

        signature = self._data.get("Signature")
        if not signature:
            self._verified = False
            return self._verified

        # Decode the signature from base64
        signature = bytes(base64.b64decode(signature))

        # Get the message to sign
        sign_bytes = self._get_bytes_to_sign()
        if not sign_bytes:
            self._verified = False
            return self._verified

        if not self.certificate:
            self._verified = False
            return self._verified

        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
        except ImportError:
            raise ImproperlyConfigured(self._REQ_DEP_TMPL % "`cryptography`")

        # Extract the public key
        pkey = self.certificate.public_key()

        # Use the public key to verify the signature.
        try:
            # The details here do not appear to be documented, but the
            # algorithm and padding choices work in testing, which should mean
            # they're the right ones.
            pkey.verify(
                signature,
                sign_bytes,
                padding.PKCS1v15(),
                hashes.SHA1(),
            )
        except InvalidSignature:
            logger.warning(
                "Invalid signature on message with ID: %s",
                self._data.get("MessageId"),
            )
            self._verified = False
        else:
            self._verified = True
        return self._verified

    @property
    def certificate(self):
        """
        Retrieves the certificate used to sign the event message.

        :returns: None if the cert cannot be retrieved. Else, gets the cert
        caches it, and returns it, or simply returns it if already cached.
        """
        cert_url = self._get_cert_url()
        if not cert_url:
            return None

        if cert_url in _CERT_CACHE:
            return _CERT_CACHE[cert_url]

        # Only load certificates from a certain domain?
        # Without some kind of trusted domain check, any old joe could
        # craft a event message and sign it using his own certificate
        # and we would happily load and verify it.
        try:
            import requests
            from requests import RequestException
        except ImportError:
            raise ImproperlyConfigured(self._REQ_DEP_TMPL % "`requests`")

        try:
            from cryptography import x509
        except ImportError:
            raise ImproperlyConfigured(self._REQ_DEP_TMPL % "`cryptography`")

        # We use requests because it verifies the https certificate when
        # retrieving the signing certificate. If https was somehow hijacked
        # then all bets are off.
        try:
            response = requests.get(cert_url, timeout=10)
            response.raise_for_status()
        except RequestException as exc:
            logger.warning(
                "Network error downloading certificate from %s: %s",
                cert_url,
                exc,
            )
            _CERT_CACHE[cert_url] = None
            return _CERT_CACHE[cert_url]

        # Handle errors loading the certificate.
        # If the certificate is invalid then return
        # false as we couldn't verify the message.
        try:
            _CERT_CACHE[cert_url] = x509.load_pem_x509_certificate(response.content)
        except ValueError as e:
            logger.warning('Could not load certificate from %s: "%s"', cert_url, e)
            _CERT_CACHE[cert_url] = None

        return _CERT_CACHE[cert_url]

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
            if "amazonaws.com" in trusted_domain:
                if not SES_REGEX_CERT_URL.match(cert_url):
                    if len(parts) < 4:
                        return None
                    else:
                        logger.warning('Possible security risk for: "%s"', cert_url)
                        logger.warning(
                            "It is strongly recommended to configure the full domain in EVENT_CERT_DOMAINS. "
                            "See v3.5.0 release notes for more details."
                        )

            if url_obj.netloc.split(".")[-len(parts) :] == parts:
                return cert_url

        return None

    def _get_bytes_to_sign(self):
        """
        Creates the message used for signing SNS notifications.
        This is used to verify the bounce message when it is received.
        """

        # Depending on the message type the fields to add to the message
        # differ so we handle that here.
        msg_type = self._data.get("Type")
        if msg_type == "Notification":
            fields_to_sign = [
                "Message",
                "MessageId",
                "Subject",
                "Timestamp",
                "TopicArn",
                "Type",
            ]
        elif msg_type == "SubscriptionConfirmation" or msg_type == "UnsubscribeConfirmation":
            fields_to_sign = [
                "Message",
                "MessageId",
                "SubscribeURL",
                "Timestamp",
                "Token",
                "TopicArn",
                "Type",
            ]
        else:
            # Unrecognized type
            logger.warning('Unrecognized SNS message Type: "%s"', msg_type)
            return None

        bytes_to_sign = []
        for field in fields_to_sign:
            field_value = self._data.get(field)
            if not field_value:
                continue

            # Some notification types do not have all fields. Only add fields
            # with values.
            bytes_to_sign.append(f"{field}\n{field_value}\n")

        return "".join(bytes_to_sign).encode()


def BounceMessageVerifier(*args, **kwargs):  # noqa: N802
    warnings.warn(
        "utils.BounceMessageVerifier is deprecated. It is renamed to EventMessageVerifier.",
        RemovedInDjangoSES20Warning,
    )

    # parameter name is renamed from bounce_dict to notification.
    if "bounce_dict" in kwargs:
        kwargs["notification"] = kwargs["bounce_dict"]
        del kwargs["bounce_dict"]

    return EventMessageVerifier(*args, **kwargs)


def verify_event_message(notification):
    """
    Verify an SES/SNS event notification message.
    """
    verifier = EventMessageVerifier(notification)
    return verifier.is_verified()


def verify_event_topic(notification):
    """
    Return True if the notification's TopicArn is trusted.

    An empty AWS_SNS_EVENT_TRUSTED_TOPIC_ARNS preserves historical behaviour
    of accepting any topic.
    """
    trusted_arns = settings.EVENT_TRUSTED_TOPIC_ARNS
    if not trusted_arns:
        return True
    return notification.get("TopicArn") in trusted_arns


def is_trusted_sns_subscribe_url(url):
    """
    Return True if url is an https SNS service endpoint.

    SubscribeURL is fetched to confirm a subscription. urlopen() accepts
    file:// and other schemes, so constrain the fetch to SNS HTTPS hosts.
    """
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").rstrip(".")
    return bool(SES_REGEX_SNS_ENDPOINT_HOST.match(host))


def verify_bounce_message(msg):
    """
    Verify an SES/SNS bounce(event) notification message.
    """
    warnings.warn(
        "utils.verify_bounce_message is deprecated. It is renamed to verify_event_message.",
        RemovedInDjangoSES20Warning,
    )
    return verify_event_message(msg)


def confirm_sns_subscription(notification):
    if not verify_event_topic(notification):
        logger.warning(
            "Rejected subscription confirmation from untrusted topic: %s",
            notification.get("TopicArn"),
            extra={
                "notification": notification,
            },
        )
        return

    logger.info(
        "Received subscription confirmation: TopicArn: %s",
        notification.get("TopicArn"),
        extra={
            "notification": notification,
        },
    )

    # Get the subscribe url and hit the url to confirm the subscription.
    subscribe_url = notification.get("SubscribeURL")
    if not is_trusted_sns_subscribe_url(subscribe_url):
        logger.warning(
            'Untrusted SubscribeURL: "%s"',
            subscribe_url,
            extra={
                "notification": notification,
            },
        )
        return

    try:
        urlopen(subscribe_url).read()
    except URLError as e:
        # Some kind of error occurred when confirming the request.
        logger.error(
            'Could not confirm subscription: "%s"',
            e,
            extra={
                "notification": notification,
            },
            exc_info=True,
        )


def get_permanent_bounced_recipients_from_bounce_obj(bounce_obj: dict) -> list:
    """Extracts the permanently bounced recipients as a list of SES ``bouncedRecipients`` dicts.

    SES decides whether a bounce is permanent, in ``bounceType``. A ``Transient`` bounce, such as a full mailbox or
    a message that is too large, often carries a ``5.x.x`` status, so the status alone does not make it permanent.
    In a ``Permanent`` bounce, a recipient whose status is not ``5.x.x`` (such as ``4.0.0``, delayed) is left out.
    https://docs.aws.amazon.com/ses/latest/dg/notification-contents.html#bounce-types
    """
    if bounce_obj.get("bounceType") != "Permanent":
        return []
    bounced_recipients = bounce_obj.get("bouncedRecipients", list())
    return [br for br in bounced_recipients if br.get("status", "5").startswith("5")]


def get_permanent_bounced_emails_from_bounce_obj(bounce_obj: dict) -> list:
    """Extracts permanent bounced email addresses only as a list of strings.

    See ``get_permanent_bounced_recipients_from_bounce_obj`` for which recipients count as permanently bounced.
    """
    return [br.get("emailAddress") for br in get_permanent_bounced_recipients_from_bounce_obj(bounce_obj)]


def get_emails_from_complaint_obj(complaint_obj: dict) -> list:
    """Extracts complaint email addresses from complaint_obj
    https://docs.aws.amazon.com/ses/latest/DeveloperGuide/notification-contents.html#complaint-object
    """
    return [cr.get("emailAddress") for cr in complaint_obj.get("complainedRecipients", list())]


# The start of a line of an SMTP reply: the reply code, "-" on every line but the last, then the enhanced status code
# if the server sends one. https://www.rfc-editor.org/rfc/rfc5321#section-4.2.1
_SMTP_REPLY_PREFIX = re.compile(r"(?P<code>[2-5]\d\d)[- ](?:(?P<enhanced>[2-5]\.\d{1,3}\.\d{1,3})(?: |$))?")


def _join_smtp_reply(value):
    """Joins a multiline SMTP reply into one line, writing the reply code only once.

    ``smtp; 550-5.1.1 Foo\\n550 5.1.1 bar`` becomes ``smtp; 550 5.1.1 Foo bar``. The text before the code on the
    first line (SES writes ``smtp; ``) is kept. If any line does not start with the same codes as the first one,
    the value is returned unchanged, so no code is lost.
    """
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if len(lines) < 2:
        return value

    first = _SMTP_REPLY_PREFIX.search(lines[0])
    if not first:
        return value
    codes = (first["code"], first["enhanced"])

    texts = [lines[0][first.end() :]]
    for line in lines[1:]:
        match = _SMTP_REPLY_PREFIX.match(line)
        if not match or (match["code"], match["enhanced"]) != codes:
            return value
        texts.append(line[match.end() :])

    head = lines[0][: first.start()] + " ".join(code for code in codes if code)
    return " ".join([head, *texts])


def _format_reason(event, fields):
    """Builds a readable reason: the event name, then one ``label: value`` line per field SES sent.

    Whitespace inside a value, newlines included, is collapsed to single spaces, so each field stays on its line.
    """
    lines = [event]
    for label, value in fields:
        value = " ".join(str(value).split()) if value else ""
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def get_bounce_reason(bounce_obj: dict, bounced_recipient: dict) -> str:
    """Describes why a recipient bounced, from a bounce object and one of its ``bouncedRecipients``.
    https://docs.aws.amazon.com/ses/latest/dg/notification-contents.html#bounce-object
    """
    diagnostic_code = bounced_recipient.get("diagnosticCode")
    if isinstance(diagnostic_code, str):
        diagnostic_code = _join_smtp_reply(diagnostic_code)

    return _format_reason(
        "Bounce",
        [
            ("Bounce type", bounce_obj.get("bounceType")),
            ("Bounce sub-type", bounce_obj.get("bounceSubType")),
            ("Status", bounced_recipient.get("status")),
            ("Action", bounced_recipient.get("action")),
            ("Diagnostic code", diagnostic_code),
            ("Reporting MTA", bounce_obj.get("reportingMTA")),
            ("Timestamp", bounce_obj.get("timestamp")),
            ("Feedback ID", bounce_obj.get("feedbackId")),
        ],
    )


def get_complaint_reason(complaint_obj: dict) -> str:
    """Describes a complaint, from a complaint object.
    https://docs.aws.amazon.com/ses/latest/dg/notification-contents.html#complaint-object
    """
    return _format_reason(
        "Complaint",
        [
            ("Complaint feedback type", complaint_obj.get("complaintFeedbackType")),
            ("Complaint sub-type", complaint_obj.get("complaintSubType")),
            ("User agent", complaint_obj.get("userAgent")),
            ("Timestamp", complaint_obj.get("timestamp")),
            ("Feedback ID", complaint_obj.get("feedbackId")),
        ],
    )


def filter_blacklisted_recipients(addresses):
    from django_ses import models

    """Remove blacklisted emails from addresses"""
    if isinstance(addresses, str):
        addresses = [addresses]

    emails = [parseaddr(recipient)[1].lower() for recipient in addresses]
    qs = models.BlacklistedEmail.objects.filter(email__in=emails)
    excluded_emails = set(qs.values_list("email", flat=True))
    return [email for email in emails if email not in excluded_emails]


def blacklist_email(email, reason):
    """Blacklists one email, and stores ``reason`` if the email is already blacklisted with a blank reason.

    Returns ``(obj, action)``, where ``action`` is ``"created"``, ``"reason_stored"`` or ``"unchanged"``.
    """
    from django_ses import models

    obj, created = models.BlacklistedEmail.objects.get_or_create(email=email, defaults={"reason": reason})
    if created:
        return obj, "created"
    if not obj.reason and reason:
        # Filter on the blank reason too, so a reason stored in the meantime is not overwritten.
        if models.BlacklistedEmail.objects.filter(pk=obj.pk, reason="").update(reason=reason):
            obj.reason = reason
            return obj, "reason_stored"
        obj.refresh_from_db(fields=["reason"])
    return obj, "unchanged"


def blacklist_recipients(reasons):
    """Blacklists each email in ``reasons``, a dict that maps an email to why it is blacklisted.

    An email that is already blacklisted keeps its reason, unless that reason is blank (such as a row that
    existed before the ``reason`` field was added): then it gets the new one.
    """
    from django_ses import models

    reasons = {email.lower(): reason for email, reason in reasons.items() if email}
    if len(reasons) == 0:
        return

    # If we received only 1 recipients, don't waste extra queries trying to find
    # out if the recipient has already been blacklisted; just attempt to
    # blacklist it.
    if len(reasons) == 1:
        ((email, reason),) = reasons.items()
        blacklist_email(email, reason)
        return

    qs = models.BlacklistedEmail.objects.filter(email__in=reasons.keys())
    blacklisted_emails = set(qs.values_list("email", flat=True))
    unblacklisted_emails = [email for email in reasons if email not in blacklisted_emails]

    # Try to bulk-insert the unblacklisted emails. If the operation fails (a
    # possibility only when using Oracle because it doesn't support
    # ignore_conflicts), fallback to one-by-one insertion.
    try:
        models.BlacklistedEmail.objects.bulk_create(
            [models.BlacklistedEmail(email=email, reason=reasons[email]) for email in unblacklisted_emails],
            ignore_conflicts=True,
        )
    except NotSupportedError:  # Oracle doesn't support "ignore_conflicts"
        for email, reason in reasons.items():
            blacklist_email(email, reason)
        return

    # ignore_conflicts leaves existing rows unchanged, so give a reason to the rows of this batch that have none.
    blank = list(models.BlacklistedEmail.objects.filter(email__in=reasons.keys(), reason=""))
    for obj in blank:
        obj.reason = reasons[obj.email]
    models.BlacklistedEmail.objects.bulk_update(blank, ["reason"])
