from django.test import SimpleTestCase

from django_ses.utils import get_bounce_reason


class BounceReasonTestCase(SimpleTestCase):
    def _diagnostic_code_line(self, diagnostic_code):
        """Returns the "Diagnostic code" line of the reason for a bounce with ``diagnostic_code``."""
        reason = get_bounce_reason(
            {"bounceType": "Permanent", "bounceSubType": "General", "timestamp": "2012-05-25T14:59:38.605-07:00"},
            {"emailAddress": "recipient1@example.com", "status": "5.1.1", "diagnosticCode": diagnostic_code},
        )
        lines = reason.split("\n")
        # One line per field, whatever the diagnostic code holds.
        self.assertEqual(
            [line.split(":")[0] for line in lines],
            ["Bounce", "Bounce type", "Bounce sub-type", "Status", "Diagnostic code", "Timestamp"],
        )
        return lines[4]

    def test_multiline_smtp_reply_is_joined(self):
        diagnostic_code = (
            "smtp; 550-5.1.1 The email account that you tried to reach does not exist. Please try\r\n"
            "550-5.1.1 double-checking the recipient's email address for typos or\r\n"
            "550 5.1.1 https://support.google.com/mail/?p=NoSuchUser"
        )

        self.assertEqual(
            self._diagnostic_code_line(diagnostic_code),
            "Diagnostic code: smtp; 550 5.1.1 The email account that you tried to reach does not exist. "
            "Please try double-checking the recipient's email address for typos or "
            "https://support.google.com/mail/?p=NoSuchUser",
        )

    def test_multiline_smtp_reply_without_enhanced_code_is_joined(self):
        diagnostic_code = "smtp; 550-No such user here\n550 Please check the address"

        self.assertEqual(
            self._diagnostic_code_line(diagnostic_code),
            "Diagnostic code: smtp; 550 No such user here Please check the address",
        )

    def test_multiline_smtp_reply_with_different_codes_keeps_them(self):
        diagnostic_code = "smtp; 550-5.1.1 User unknown\n550 5.7.1 Relaying denied"

        self.assertEqual(
            self._diagnostic_code_line(diagnostic_code),
            "Diagnostic code: smtp; 550-5.1.1 User unknown 550 5.7.1 Relaying denied",
        )

    def test_multiline_text_without_codes_is_collapsed(self):
        diagnostic_code = "Unable to deliver:\n  the   mailbox\tis disabled"

        self.assertEqual(
            self._diagnostic_code_line(diagnostic_code),
            "Diagnostic code: Unable to deliver: the mailbox is disabled",
        )

    def test_single_line_smtp_reply_is_unchanged(self):
        self.assertEqual(
            self._diagnostic_code_line("smtp; 550 5.1.1 user unknown"),
            "Diagnostic code: smtp; 550 5.1.1 user unknown",
        )
