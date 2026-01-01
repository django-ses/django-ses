"""
Integration tests using LocalStack for AWS SES.

LocalStack Limitations:
- SES v2 API not fully supported (USE_SES_V2=False required)
- Some advanced SES features may not be available
- Email delivery simulation only (no actual SMTP)

Setup:
    Local: docker-compose up -d
    CI: Automatically configured in GitHub Actions

Environment Variables:
    LOCALSTACK_ENDPOINT: LocalStack endpoint URL (default: http://localhost:4566)
"""

from __future__ import annotations

import email
import os
import time
from email.message import Message
from unittest import SkipTest

import requests
from django.core.mail import send_mail
from django.test import TestCase, override_settings

from tests.helper import decode_email_header

LOCALSTACK_ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566")


@override_settings(
    EMAIL_BACKEND="django_ses.SESBackend",
    AWS_SES_REGION_ENDPOINT_URL=LOCALSTACK_ENDPOINT,
    AWS_SES_ACCESS_KEY_ID="test",
    AWS_SES_SECRET_ACCESS_KEY="test",
    AWS_SES_REGION_NAME="eu-central-1",
    USE_SES_V2=False,  # LocalStack does not support v2 yet
)
class LocalStackIntegrationTest(TestCase):
    """
    Integration tests using LocalStack for AWS SES.

    These tests require LocalStack to be running. Start it with:
        docker-compose up -d
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # Validate LocalStack is accessible before running tests
        try:
            response = requests.get(f"{LOCALSTACK_ENDPOINT}/_localstack/health", timeout=1)
            response.raise_for_status()

            # Verify SES service is available
            health_data = response.json()
            if health_data.get("services", {}).get("ses") != "running":
                raise SkipTest("SES service not available in LocalStack")

        except requests.RequestException as e:
            raise SkipTest(f"LocalStack not accessible at {LOCALSTACK_ENDPOINT}: {e}")

    def tearDown(self) -> None:
        """Clean up the local stack after each test"""
        # Delete all emails from LocalStack
        try:
            requests.delete(f"{LOCALSTACK_ENDPOINT}/_aws/ses")
        except Exception:
            # Ignore errors during cleanup
            pass

    def _get_sent_messages(self, email_address: str | None = None) -> list[dict]:
        """
        Retrieve messages from LocalStack using its internal API.

        Args:
            email_address: Optional email address to filter messages

        Returns:
            List of sent messages from LocalStack
        """
        # Poll LocalStack's internal SES API to retrieve sent messages
        max_attempts = 10
        sleep_interval = 0.1  # 100ms between attempts

        params = {}
        if email_address:
            params["email"] = email_address

        for _ in range(max_attempts):
            response = requests.get(f"{LOCALSTACK_ENDPOINT}/_aws/ses", params=params)

            if response.status_code == 200:
                messages = response.json().get("messages", [])
                if messages:
                    return messages

            time.sleep(sleep_interval)

        # Provide helpful error message
        self.fail(
            f"No messages found in LocalStack after {max_attempts * sleep_interval}s. "
            f"Filter: {params if params else 'none'}"
        )
        return []

    def _verify_sent_email(
        self,
        from_email: str,
        expected_subject: str,
        expected_to: str,
        expected_body: str,
    ) -> None:
        """
        Verify that an email was sent through LocalStack with expected content.

        Args:
            from_email: Email address to filter messages by
            expected_subject: Expected email subject
            expected_to: Expected recipient email address
            expected_body: Expected email body content
        """
        # Verify the message was actually sent through LocalStack
        messages = self._get_sent_messages(email_address=from_email)
        self.assertGreater(len(messages), 0, "No messages found in LocalStack")

        # Verify message content
        sent_message = messages[0]

        # Parse the raw email data
        raw_data = sent_message.get("RawData", "")
        parsed_email: Message = email.message_from_string(raw_data)

        # Verify email headers and content
        self.assertEqual(decode_email_header(parsed_email["Subject"]), expected_subject)
        self.assertEqual(decode_email_header(parsed_email["From"]), from_email)
        self.assertEqual(decode_email_header(parsed_email["To"]), expected_to)

        email_body = parsed_email.get_payload()
        self.assertEqual(email_body.strip(), expected_body)

    def test_send_simple_email(self) -> None:
        """Test sending a simple email through LocalStack SES v1."""
        from_email = "test@example.com"
        to_email = "to@example.com"
        subject = "Test Subject"
        body = "Test Body"

        result = send_mail(subject, body, from_email, [to_email])

        # Verify email was sent (returns 1 for success)
        self.assertEqual(result, 1)

        # Verify the email content
        self._verify_sent_email(
            from_email=from_email,
            expected_subject=subject,
            expected_to=to_email,
            expected_body=body,
        )

    def test_send_email_with_unicode(self) -> None:
        """Test sending an email with unicode through LocalStack SES v1."""
        from_email = "Unicode Name óóóóóó <test@example.com>"
        to_email = "Recipient Ñame <to@example.com>"
        subject = "Scandinavian Tëst Sübject"
        body = "Sören & Björn"

        result = send_mail(subject, body, from_email, [to_email])

        # Verify email was sent (returns 1 for success)
        self.assertEqual(result, 1)

        # Verify the email content
        self._verify_sent_email(
            from_email=from_email,
            expected_subject=subject,
            expected_to=to_email,
            expected_body=body,
        )
