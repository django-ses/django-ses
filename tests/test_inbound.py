from django.test import TestCase

from django_ses.inbound import S3Handler, SnsHandler, UnprocessableError
from tests.mocks import (
    get_mock_received_s3,
    get_mock_received_sns,
)


class InbounceSnsTestCase(TestCase):
    def test_happy_path(self):
        mail_obj, content, receipt, notification = get_mock_received_sns()

        class MyReceiver(SnsHandler):
            def process(self):
                self.test_result_subject = self.email.get("subject")
                self.test_result_plain_text = self.email.get("plain_text")
                self.test_result_attachments = self.email.get("attachments")

        handler = MyReceiver(
            mail_obj=mail_obj, receipt=receipt, raw_message=notification)
        handler.handle(content=content)

        self.assertEqual(handler.test_result_subject, "test")
        self.assertEqual(handler.test_result_plain_text, "hey!!\n")
        self.assertEqual(len(handler.test_result_attachments), 1)
        attachment = handler.test_result_attachments[0]
        self.assertEqual(attachment.get("filename"), "attachmnet.png")
        self.assertEqual(attachment.get("content_type"), "image/png")
        self.assertEqual(len(attachment.get("data")), 3013)

    def test_bad_content(self):
        mail_obj, content, receipt, notification = get_mock_received_sns()
        handler = SnsHandler(
            mail_obj=mail_obj, receipt=receipt, raw_message=notification)

        with self.assertLogs('django_ses', level='INFO') as cm:
          with self.assertRaises(UnprocessableError):
              handler.handle(content="bad content that is not base64!")

          self.assertEqual(
              cm.output[-1],
              "ERROR:django_ses.inbound:Content couldn't be decoded with base64. Invalid content?")

    def test_wrong_handler(self):
        mail_obj, content, receipt, notification = get_mock_received_s3()
        handler = SnsHandler(
            mail_obj=mail_obj, receipt=receipt, raw_message=notification)

        with self.assertLogs('django_ses', level='INFO') as cm:
          with self.assertRaises(UnprocessableError):
              handler.handle(content=content)

          self.assertEqual(
              cm.output[-1],
              "ERROR:django_ses.inbound:Received action type (S3) or encoding (None) can't be handled by this handler")


class InbounceS3TestCase(TestCase):
    def test_happy_path(self):
        mail_obj, content, receipt, notification = get_mock_received_s3()

        class MyReceiver(S3Handler):
            def prepare_content(self, _):
                return b"hey!!\n"

            def process(self):
                self.test_result_subject = self.email.get("subject")
                self.test_result_plain_text = self.email.get("plain_text")
                self.test_result_attachments = self.email.get("attachments")

        handler = MyReceiver(
            mail_obj=mail_obj, receipt=receipt, raw_message=notification)
        handler.handle(content=content)

        self.assertEqual(handler.test_result_subject, "test")
        self.assertEqual(handler.test_result_plain_text, "hey!!\n")
        self.assertEqual(handler.test_result_attachments, [])

    def test_wrong_handler(self):
        mail_obj, content, receipt, notification = get_mock_received_sns()
        handler = S3Handler(
            mail_obj=mail_obj, receipt=receipt, raw_message=notification)

        with self.assertLogs('django_ses', level='INFO') as cm:
          with self.assertRaises(UnprocessableError):
              handler.handle(content=content)

          self.assertEqual(
              cm.output[-1],
              "ERROR:django_ses.inbound:Received action type (SNS) can't be handled by this handler")
