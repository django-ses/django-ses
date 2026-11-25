"""Reading SES bounce and complaint events: which recipients they affect, and why."""

import re


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
