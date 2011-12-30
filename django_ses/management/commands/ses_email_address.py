#!/usr/bin/env python
# encoding: utf-8
from optparse import make_option

from boto.regioninfo import RegionInfo
from boto.ses import SESConnection

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Verify, delete or list SES email addresses"""

    option_list = BaseCommand.option_list + (
        # -v conflicts with verbose, so use -a
        make_option("-a", "--add", dest="add", default=False,
            help="""Adds an email to your verified email address list.
                    This action causes a confirmation email message to be
                    sent to the specified address."""),
        make_option("-d", "--delete", dest="delete", default=False,
            help="Removes an email from your verified emails list"),
        make_option("-l", "--list", dest="list", default=False,
            action="store_true", help="Outputs all verified emails"),
    )

    def handle(self, *args, **options):

        verbosity = options.get('verbosity', 0)
        add_email = options.get('add', False)
        delete_email = options.get('delete', False)
        list_emails = options.get('list', False)

        access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        region = RegionInfo(
            name=getattr(settings, 'AWS_SES_REGION_NAME',
                SESConnection.DefaultRegionName),
            endpoint=getattr(settings, 'AWS_SES_REGION_ENDPOINT',
                SESConnection.DefaultRegionEndpoint))

        connection = SESConnection(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=access_key,
                region=region)

        if add_email:
            if verbosity != '0':
                print "Adding email: %s" % add_email
            connection.verify_email_address(add_email)
        elif delete_email:
            if verbosity != '0':
                print "Removing email: %s" % delete_email
            connection.delete_verified_email_address(delete_email)
        elif list_emails:
            if verbosity != '0':
                print "Fetching list of verified emails:"
            response = connection.list_verified_email_addresses()
            emails = response['ListVerifiedEmailAddressesResponse'][
                'ListVerifiedEmailAddressesResult']['VerifiedEmailAddresses']
            for email in emails:
                print email
