"""Adding emails to the blacklist, and filtering blacklisted emails out of recipients."""

from email.utils import parseaddr

from django.db import NotSupportedError


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
