import base64
import binascii
import logging
from email import policy
from email.parser import BytesParser

import boto3

from django_ses import settings

logger = logging.getLogger(__name__)


class UnprocessableError(Exception):
    pass


def parse_email(content):
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

    return plain_text, html_text, attachments


def _get_common_headers(mail_obj):
    common = mail_obj.get('commonHeaders', {})

    return {
        'subject': common.get('subject'),
        'to': common.get('to'),
        'message_id': common.get('messageId'),
        'date': common.get('date'),
    }


def raw_handler(*args, **kwargs):
    return kwargs


def s3_handler(mail_obj, content, receipt, raw_message):
    common_headers = _get_common_headers(mail_obj)
    action = receipt.get('action', {})

    action_type = action.get('type')
    if action_type != 'S3':
        logger.error(
            f'Received action type ({action_type}) can\'t be handled by this '
            f'handler')
        raise UnprocessableError

    bucket_name = action.get('bucketName')
    object_key = action.get('objectKey')

    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.ACCESS_KEY,
        aws_secret_access_key=settings.SECRET_KEY,
        aws_session_token=settings.SESSION_TOKEN,
    )

    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    content = response['Body'].read()

    plain_text, html_text, attachments = parse_email(content)

    return {
        **common_headers,
        'plain_text': plain_text,
        'html_text': html_text,
        'attachments': attachments,
    }


def sns_handler(mail_obj, content, receipt, raw_message):
    common_headers = _get_common_headers(mail_obj)
    action = receipt.get('action', {})

    action_type = action.get('type')
    encoding = action.get('encoding')
    if action_type != 'SNS' or encoding != 'BASE64':
        logger.error(
            f'Received action type ({action_type}) or encoding ({encoding}) '
            f'can\'t be handled by this handler')
        raise UnprocessableError

    try:
        content = base64.b64decode(content, validate=True)
    except binascii.Error:
        logger.error(
            'Content couldn\'t be decoded with base64. Invalid content?')
        raise UnprocessableError

    plain_text, html_text, attachments = parse_email(content)

    return {
        **common_headers,
        'plain_text': plain_text,
        'html_text': html_text,
        'attachments': attachments,
    }
