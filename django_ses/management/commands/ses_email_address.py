#!/usr/bin/env python
# encoding: utf-8
from optparse import make_option

import boto3
from django.core.management.base import BaseCommand

from django_ses import settings


def _add_options(target):
    return (
        target(
            '-a',
            '--add',
            dest='add',
            default=False,
            help="""Adds an email to your verified email address list.
                    This action causes a confirmation email message to be
                    sent to the specified address."""
        ),
        target(
            '-d',
            '--delete',
            dest='delete',
            default=False,
            help='Removes an email from your verified emails list'
        ),
        target(
            '-l',
            '--list',
            dest='list',
            default=False,
            action='store_true',
            help='Outputs all verified emails'
        )
    )


class Command(BaseCommand):
    """Verify, delete or list SES email addresses"""

    if hasattr(BaseCommand, 'option_list'):
        # Django < 1.10
        option_list = BaseCommand.option_list + _add_options(make_option)
    else:
        # Django >= 1.10
        def add_arguments(self, parser):
            _add_options(parser.add_argument)

    def handle(self, *args, **options):

        verbosity = options.get('verbosity', 0)
        add_email = options.get('add', '')
        delete_email = options.get('delete', '')
        list_emails = options.get('list', False)

        access_key_id = settings.ACCESS_KEY
        access_key = settings.SECRET_KEY

        connection = boto3.client(
            'ses',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=access_key,
            region_name=settings.AWS_SES_REGION_NAME,
            endpoint_url=settings.AWS_SES_REGION_ENDPOINT_URL,
        )

        if add_email:
            if verbosity != '0':
                print("Adding email: " + add_email)
            connection.verify_email_address(EmailAddress=add_email)
        elif delete_email:
            if verbosity != '0':
                print("Removing email: " + delete_email)
            connection.delete_verified_email_address(EmailAddress=delete_email)
        elif list_emails:
            if verbosity != '0':
                print("Fetching list of verified emails:")
            response = connection.list_verified_email_addresses()
            emails = response['VerifiedEmailAddresses']
            for email in emails:
                print(email)
