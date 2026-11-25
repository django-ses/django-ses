"""Helpers for SES events and the blacklist.

The code lives in submodules: ``sns`` (SNS message verification and subscriptions), ``events`` (reading bounce and
complaint events) and ``blacklist``. Everything public is re-exported here, so ``django_ses.utils.<name>`` keeps
working.
"""

from django_ses.utils.blacklist import blacklist_email, blacklist_recipients, filter_blacklisted_recipients
from django_ses.utils.events import (
    get_bounce_reason,
    get_complaint_reason,
    get_emails_from_complaint_obj,
    get_permanent_bounced_emails_from_bounce_obj,
    get_permanent_bounced_recipients_from_bounce_obj,
)
from django_ses.utils.sns import (
    _CERT_CACHE,  # noqa: F401 (kept importable from here, like before the split)
    SES_REGEX_CERT_URL,
    SES_REGEX_SNS_ENDPOINT_HOST,
    BounceMessageVerifier,
    EventMessageVerifier,
    clear_cert_cache,
    confirm_sns_subscription,
    is_trusted_sns_subscribe_url,
    verify_bounce_message,
    verify_event_message,
    verify_event_topic,
)

__all__ = [
    # sns
    "SES_REGEX_CERT_URL",
    "SES_REGEX_SNS_ENDPOINT_HOST",
    "BounceMessageVerifier",
    "EventMessageVerifier",
    "clear_cert_cache",
    "confirm_sns_subscription",
    "is_trusted_sns_subscribe_url",
    "verify_bounce_message",
    "verify_event_message",
    "verify_event_topic",
    # events
    "get_bounce_reason",
    "get_complaint_reason",
    "get_emails_from_complaint_obj",
    "get_permanent_bounced_emails_from_bounce_obj",
    "get_permanent_bounced_recipients_from_bounce_obj",
    # blacklist
    "blacklist_email",
    "blacklist_recipients",
    "filter_blacklisted_recipients",
]
