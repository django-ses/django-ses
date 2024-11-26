import base64
import binascii
import logging
from email import policy
from email.parser import BytesParser
from typing import TypedDict

import boto3

from django_ses import settings

logger = logging.getLogger(__name__)


class InboundEmail(TypedDict):
    plain_text: str
    html_text: str
    attachments: list
    subject: str
    to: list
    message_id: str
    date: str


class UnprocessableError(Exception):
    pass


class BaseHandler:
  def __init__(self, mail_obj, receipt, raw_message):
      self.mail_obj = mail_obj
      self.receipt = receipt
      self.raw_message = raw_message
      self.action = receipt.get('action', {})

  def check_action_compatibility(self):
      """
      This method should raise UnprocessableError if the received payload from
      SES can't be processed
      """
      pass

  def prepare_content(self, content):
      return content

  def parse_email(self, content) -> InboundEmail:
      parser = BytesParser(policy=policy.default)
      email_message = parser.parsebytes(content)

      plain_text = ''
      html_text = ''
      attachments = []

      for part in email_message.walk():
          content_type = part.get_content_type()
          content_disposition = part.get('Content-Disposition', '')

          # Handle plain text
          if content_type == 'text/plain' and 'attachment' not in content_disposition:
              plain_text = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')

          # Handle HTML
          elif content_type == 'text/html' and 'attachment' not in content_disposition:
              html_text = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')

          # Handle attachments
          elif 'attachment' in content_disposition:
              attachment = {
                  'filename': part.get_filename(),
                  'content_type': content_type,
                  'data': part.get_payload(decode=True)
              }
              attachments.append(attachment)

      common = self.mail_obj.get('commonHeaders', {})

      return InboundEmail(
          plain_text=plain_text,
          html_text=html_text,
          attachments=attachments,
          subject = common.get('subject'),
          to = common.get('to'),
          message_id = common.get('messageId'),
          date = common.get('date'),
      )

  def process(self):
      raise NotImplementedError

  def handle(self, content=None, *args, **kwargs):
      self.check_action_compatibility()

      content = self.prepare_content(content)

      self.email = self.parse_email(content)

      self.process()


class S3Handler(BaseHandler):
  def check_action_compatibility(self):
      action_type = self.action.get('type')
      if action_type != 'S3':
          logger.error(
              f'Received action type ({action_type}) can\'t be handled by this '
              f'handler')
          raise UnprocessableError

  def prepare_content(self, content):
      bucket_name = self.action.get('bucketName')
      object_key = self.action.get('objectKey')

      s3_client = boto3.client(
          's3',
          aws_access_key_id=settings.AWS_SES_INBOUND_ACCESS_KEY_ID,
          aws_secret_access_key=settings.AWS_SES_INBOUND_SECRET_ACCESS_KEY,
          aws_session_token=settings.AWS_SES_INBOUND_SESSION_TOKEN,
      )

      response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
      content = response['Body'].read()

      return content


class SnsHandler(BaseHandler):
  def check_action_compatibility(self):
      action_type = self.action.get('type')
      encoding = self.action.get('encoding')
      if action_type != 'SNS' or encoding != 'BASE64':
          logger.error(
              f'Received action type ({action_type}) or encoding ({encoding}) '
              f'can\'t be handled by this handler')
          raise UnprocessableError

  def prepare_content(self, content):
      try:
          content = base64.b64decode(content, validate=True)
      except binascii.Error:
          logger.error(
              'Content couldn\'t be decoded with base64. Invalid content?')
          raise UnprocessableError

      return content
