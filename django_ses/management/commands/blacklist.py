#!/usr/bin/env python
# encoding: utf-8

from django.core.management.base import BaseCommand

from django_ses import models


def _add_options(target):
    return (
        target(
            '-a',
            '--add',
            dest='email_to_add',
            default=False,
            help='Adds an email to your blacklist'
        ),
        target(
            '-d',
            '--delete',
            dest='email_to_delete',
            default=False,
            help='Removes an email from your blacklist'
        ),
        target(
            '-l',
            '--list',
            dest='list_emails',
            default=False,
            action='store_true',
            help='Outputs all blacklisted emails'
        ),
        target(
            '-s',
            '--search',
            dest='search_email',
            default=False,
            help='Search for blacklisted emails'
        ),
    )


class Command(BaseCommand):
    """Add, delete or list blacklisted email addresses"""

    def add_arguments(self, parser):
        _add_options(parser.add_argument)

    def handle(self, *args, verbosity=0, email_to_add='', email_to_delete='',
               list_emails='', search_email='', **options):
        if email_to_add:
            if verbosity != '0':
                self.stdout.write(f"Adding email: {email_to_add}")
            models.BlacklistedEmail.objects.get_or_create(email=email_to_add.lower())
        elif email_to_delete:
            if verbosity != '0':
                self.stdout.write(f"Removing email {email_to_delete}")
            models.BlacklistedEmail.objects.filter(email=email_to_delete.lower()).delete()
        elif list_emails:
            if verbosity != '0':
                self.stdout.write("Listing blacklisted emails:")
            for obj in models.BlacklistedEmail.objects.all():
                self.stdout.write(obj.email)
        elif search_email:
            if verbosity != '0':
                self.stdout.write("Searching blacklisted emails:")
            for obj in models.BlacklistedEmail.objects.filter(email__icontains=search_email):
                self.stdout.write(obj.email)
