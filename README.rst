==========
Django-SES
==========
:Info: A Django email backend for Amazon's Simple Email Service
:Author: Harry Marr (http://github.com/hmarr, http://twitter.com/harrymarr)
:Collaborators: Paul Craciunoiu (http://github.com/pcraciunoiu, http://twitter.com/embrangler)

|pypi| |pypi-downloads| |build| |python| |django|

A bird's eye view
=================
Django-SES is a drop-in mail backend for Django_. Instead of sending emails
through a traditional SMTP mail server, Django-SES routes email through
Amazon Web Services' excellent Simple Email Service (SES_).

Django-SES can also receive emails using `SES Email receiving`_

.. _SES: http://aws.amazon.com/ses/
.. _Django: http://djangoproject.com
.. _SES Email receiving: https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html

Please Contribute!
==================
This project is maintained, but not actively used by the maintainer. Interested
in helping maintain this project? Reach out via GitHub Issues if you're actively
using `django-ses` and would be interested in contributing to it.


Changelog
=========

For details about each release, see the GitHub releases page: https://github.com/django-ses/django-ses/releases or CHANGES.md.


Using Django directly
=====================

Amazon SES allows you to also setup usernames and passwords. If you do configure
things that way, you do not need this package. The Django default email backend
is capable of authenticating with Amazon SES and correctly sending email.

Using django-ses gives you additional features like deliverability reports that
can be hard and/or cumbersome to obtain when using the SMTP interface.


Why SES instead of SMTP?
========================
Configuring, maintaining, and dealing with some complicated edge cases can be
time-consuming. Sending emails with Django-SES might be attractive to you if:

* You don't want to maintain mail servers.
* You are already deployed on EC2 (In-bound traffic to SES is free from EC2
  instances).
* You need to send a high volume of email.
* You don't want to have to worry about PTR records, Reverse DNS, email
  whitelist/blacklist services.
* You want to improve delivery rate and inbox cosmetics by DKIM signing
  your messages using SES's Easy DKIM feature.
* Django-SES is a truely drop-in replacement for the default mail backend.
  Your code should require no changes.

Why SES instead of IMAP/POP?
============================

Configuring, maintaining, and dealing with some complicated edge cases can be
time-consuming. REceiving emails with Django-SES might be attractive to you if:

* You don't want to maintain mail servers.
* You want programatic access to received emails.
* You want to react to received emails as soon as they are received.

Getting going
=============
Assuming you've got Django_ installed, you'll just need to install django-ses::

    pip install django-ses


To receive bounces or webhook events install the events "extra"::

    pip install django-ses[events]

Add the following to your settings.py::

    EMAIL_BACKEND = 'django_ses.SESBackend'

    # These are optional if you are using AWS IAM Roles https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
    AWS_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
    AWS_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'
    # https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html
    AWS_SESSION_PROFILE = 'YOUR-PROFILE-NAME'
    # Additionally, if you are not using the default AWS region of us-east-1,
    # you need to specify a region, like so:
    AWS_SES_REGION_NAME = 'us-west-2'
    AWS_SES_REGION_ENDPOINT = 'email.us-west-2.amazonaws.com'

    # If you want to use the SESv2 client
    USE_SES_V2 = True

Alternatively, instead of `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, you
can include the following two settings values. This is useful in situations
where you would like to use a separate access key to send emails via SES than
you would to upload files via S3::

    AWS_SES_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
    AWS_SES_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'

Now, when you use ``django.core.mail.send_mail``, Simple Email Service will
send the messages by default.

Since SES imposes a rate limit and will reject emails after the limit has been
reached, django-ses will attempt to conform to the rate limit by querying the
API for your current limit and then sending no more than that number of
messages in a two-second period (which is half of the rate limit, just to
be sure to stay clear of the limit). This is controlled by the following setting:

    AWS_SES_AUTO_THROTTLE = 0.5 # (default; safety factor applied to rate limit)

To turn off automatic throttling, set this to None.

Check out the ``example`` directory for more information.

Monitoring email status using Amazon Simple Notification Service (Amazon SNS)
=============================================================================
To set this up, install `django-ses` with the `events` extra::

    pip install django-ses[events]

Then add a event url handler in your `urls.py`::

    from django.urls import re_path
    from django_ses.views import SESEventWebhookView
    from django.views.decorators.csrf import csrf_exempt
    urlpatterns = [ ...
            re_path(r'^ses/event-webhook/$', SESEventWebhookView.as_view(), name='handle-event-webhook'),
            ...
    ]

SESEventWebhookView handles bounce, complaint, send, delivery, open and click events.
It is also capable of auto confirming subscriptions, it handles `SubscriptionConfirmation` notification.

On AWS
-------
1. Add an SNS topic.

2. In SES setup an SNS destination in "Configuration Sets". Use this
configuration set by setting ``AWS_SES_CONFIGURATION_SET``. Set the topic
to what you created in 1.

3. Add an https subscriber to the topic. (eg. https://www.yourdomain.com/ses/event-webhook/)
Do not check "Enable raw message delivery".


Bounces
-------
Using signal 'bounce_received' for manager bounce email. For example::

    from django_ses.signals import bounce_received
    from django.dispatch import receiver


    @receiver(bounce_received)
    def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
        # you can then use the message ID and/or recipient_list(email address) to identify any problematic email messages that you have sent
        message_id = mail_obj['messageId']
        recipient_list = mail_obj['destination']
        ...
        print("This is bounce email object")
        print(mail_obj)

The most common use case for irrecoverable bounces (status ``5xx``) is to add the
email(s) that caused the bounce to a blacklist in order to avoid sending more
emails and triggering more bounces. ``django-ses`` provides a builtin blacklist
that does this. Check ``AWS_SES_ADD_BOUNCE_TO_BLACKLIST`` and ``AWS_SES_USE_BLACKLIST``.

Complaint
---------
Using signal 'complaint_received' for manager complaint email. For example::

    from django_ses.signals import complaint_received
    from django.dispatch import receiver


    @receiver(complaint_received)
    def complaint_handler(sender, mail_obj, complaint_obj, raw_message,  *args, **kwargs):
        ...

The most common use case for complaints is to add the email(s) that caused the
complaint to a blacklist in order to avoid sending more emails and triggering
more complaints. ``django-ses`` provides a builtin blacklist that does this.
Check ``AWS_SES_ADD_COMPLAINT_TO_BLACKLIST`` and ``AWS_SES_USE_BLACKLIST``.

Message sent
------------

Use this event to know when an email was sent. Keep in mind that the
``extra_headers`` field of the message will contain the ``message_id`` that AWS
SES assigned to the email, which menas you could use this event to store emails
and cross-reference them later if/when you receive a bounce/complaint. For
example::

    from django_ses.signals import message_sent
    from django.dispatch import receiver


    @receiver(message_sent)
    def sent_handler(sender, message,  *args, **kwargs):
        ...

Send
----
Using signal 'send_received' for manager send email. For example::

    from django_ses.signals import send_received
    from django.dispatch import receiver


    @receiver(send_received)
    def send_handler(sender, mail_obj, raw_message,  *args, **kwargs):
        ...

Delivery
--------
Using signal 'delivery_received' for manager delivery email. For example::

    from django_ses.signals import delivery_received
    from django.dispatch import receiver


    @receiver(delivery_received)
    def delivery_handler(sender, mail_obj, delivery_obj, raw_message,  *args, **kwargs):
        ...

Open
----
Using signal 'open_received' for manager open email. For example::

    from django_ses.signals import open_received
    from django.dispatch import receiver


    @receiver(open_received)
    def open_handler(sender, mail_obj, open_obj, raw_message, *args, **kwargs):
        ...

Click
-----
Using signal 'click_received' for manager send email. For example::

    from django_ses.signals import click_received
    from django.dispatch import receiver


    @receiver(click_received)
    def click_handler(sender, mail_obj, click_obj, raw_message, *args, **kwargs):
        ...

Testing Signals
===============

If you would like to test your signals, you can optionally disable `AWS_SES_VERIFY_EVENT_SIGNATURES` in settings. Examples for the JSON object AWS SNS sends can be found here: https://docs.aws.amazon.com/sns/latest/dg/sns-message-and-json-formats.html#http-subscription-confirmation-json

SES Event Monitoring with Configuration Sets
============================================

You can track your SES email sending at a granular level using `SES Event Publishing`_.
To do this, you set up an SES Configuration Set and add event
handlers to it to send your events on to a destination within AWS (SNS,
Cloudwatch or Kinesis Firehose) for further processing and analysis.

To ensure that emails you send via `django-ses` will be tagged with your
SES Configuration Set, set the `AWS_SES_CONFIGURATION_SET` setting in your
settings.py to the name of the configuration set::

    AWS_SES_CONFIGURATION_SET = 'my-configuration-set-name'

This will add the `X-SES-CONFIGURATION-SET` header to all your outgoing
e-mails.

If you want to set the SES Configuration Set on a per message basis, set
`AWS_SES_CONFIGURATION_SET` to a callable.  The callable should conform to the
following prototype::

    def ses_configuration_set(message, dkim_domain=None, dkim_key=None,
                                dkim_selector=None, dkim_headers=()):
        configuration_set = 'my-default-set'
        # use message and dkim_* to modify configuration_set
        return configuration_set

    AWS_SES_CONFIGURATION_SET = ses_configuration_set

where

* `message` is a `django.core.mail.EmailMessage` object (or subclass)
* `dkim_domain` is a string containing the DKIM domain for this message
* `dkim_key` is a string containing the DKIM private key for this message
* `dkim_selector` is a string containing the DKIM selector (see DKIM, below for
  explanation)
* `dkim_headers` is a list of strings containing the names of the headers to
  be DKIM signed (see DKIM, below for explanation)

.. _SES Event Publishing: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/monitor-using-event-publishing.html


DKIM
====

Using DomainKeys_ is entirely optional, however it is recommended by Amazon for
authenticating your email address and improving delivery success rate.  See
http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/DKIM.html.
Besides authentication, you might also want to consider using DKIM in order to
remove the `via email-bounces.amazonses.com` message shown to gmail users -
see http://support.google.com/mail/bin/answer.py?hl=en&answer=1311182.

Currently there are two methods to use DKIM with Django-SES: traditional Manual
Signing and the more recently introduced Amazon Easy DKIM feature.

Easy DKIM
---------
Easy DKIM is a feature of Amazon SES that automatically signs every message
that you send from a verified email address or domain with a DKIM signature.

You can enable Easy DKIM in the AWS Management Console for SES. There you can
also add the required domain verification and DKIM records to Route 53 (or
copy them to your alternate DNS).

Once enabled and verified Easy DKIM needs no additional dependencies or
DKIM specific settings to work with Django-SES.

For more information and a setup guide see:
http://docs.aws.amazon.com/ses/latest/DeveloperGuide/easy-dkim.html

Manual DKIM Signing
-------------------
To enable Manual DKIM Signing you should install the pydkim_ package and specify values
for the ``DKIM_PRIVATE_KEY`` and ``DKIM_DOMAIN`` settings.  You can generate a
private key with a command such as ``openssl genrsa 512`` and get the public key
portion with ``openssl rsa -pubout <private.key``.  The public key should be
published to ``ses._domainkey.example.com`` if your domain is example.com.  You
can use a different name instead of ``ses`` by changing the ``DKIM_SELECTOR``
setting.

The SES relay will modify email headers such as `Date` and `Message-Id` so by
default only the `From`, `To`, `Cc`, `Subject` headers are signed, not the full
set of headers.  This is sufficient for most DKIM validators but can be overridden
with the ``DKIM_HEADERS`` setting.


Example settings.py::

   DKIM_DOMAIN = 'example.com'
   DKIM_PRIVATE_KEY = '''
   -----BEGIN RSA PRIVATE KEY-----
   xxxxxxxxxxx
   -----END RSA PRIVATE KEY-----
   '''

Example DNS record published to Route53 with boto:

   route53 add_record ZONEID ses._domainkey.example.com. TXT '"v=DKIM1; p=xxx"' 86400


.. _DomainKeys: http://dkim.org/


Identity Owners
===============

With Identity owners, you can use validated SES-domains across multiple accounts:
https://docs.aws.amazon.com/ses/latest/DeveloperGuide/sending-authorization-delegate-sender-tasks-email.html

This is useful if you got multiple environments in different accounts and still want to send mails via the same domain.

You can configure the following environment variables to use them as described in boto3-docs_::

    AWS_SES_SOURCE_ARN=arn:aws:ses:eu-central-1:012345678910:identity/example.com
    AWS_SES_FROM_ARN=arn:aws:ses:eu-central-1:012345678910:identity/example.com
    AWS_SES_RETURN_PATH_ARN=arn:aws:ses:eu-central-1:012345678910:identity/example.com

.. _boto3-docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html#SES.Client.send_raw_email


SES Sending Stats
=================

Django SES comes with two ways of viewing sending statistics.

The first one is a simple read-only report on your 24 hour sending quota,
verified email addresses and bi-weekly sending statistics.

To enable the dashboard to retrieve data from AWS, you need to update the IAM policy by adding the following actions::

    {
        "Effect": "Allow",
        "Action": [
            "ses:ListVerifiedEmailAddresses",
            "ses:GetSendStatistics"
        ],
        "Resource": "*"
    }

To generate and view SES sending statistics reports, include, update
``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ...
        'django.contrib.admin',
        'django_ses',
        # ...
    )

... and ``urls.py``::

    urlpatterns += (url(r'^admin/django-ses/', include('django_ses.urls')),)

*Optional enhancements to stats:*

Override the dashboard view
---------------------------
You can override the Dashboard view, for example, to add more context data::

    class CustomSESDashboardView(DashboardView):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context.update(**admin.site.each_context(self.request))
            return context

Then update your urls::

    urlpatterns += path('admin/django-ses/', CustomSESDashboardView.as_view(), name='django_ses_stats'),


Link the dashboard from the admin
---------------------------------
You can use adminplus for this (https://github.com/jsocol/django-adminplus)::

    from django_ses.views import DashboardView
    admin.site.register_view('django-ses', DashboardView.as_view(), 'Django SES Stats')



Store daily stats
-----------------
If you need to keep send statistics around for longer than two weeks,
django-ses also comes with a model that lets you store these. To use this
feature you'll need to run::

    python manage.py migrate

To collect the statistics, run the ``get_ses_statistics`` management command
(refer to next section for details). After running this command the statistics
will be viewable via ``/admin/django_ses/``.

Django SES Management Commands
==============================

To use these you must include ``django_ses`` in your INSTALLED_APPS.

Managing Verified Email Addresses
---------------------------------

Manage verified email addresses through the management command.

    python manage.py ses_email_address --list

Add emails to the verified email list through:

    python manage.py ses_email_address --add john.doe@example.com

Remove emails from the verified email list through:

    python manage.py ses_email_address --delete john.doe@example.com

You can toggle the console output through setting the verbosity level.

    python manage.py ses_email_address --list --verbosity 0


Collecting Sending Statistics
-----------------------------

To collect and store SES sending statistics in the database, run:

    python manage.py get_ses_statistics

Sending statistics are aggregated daily (UTC time). Stats for the latest day
(when you run the command) may be inaccurate if run before end of day (UTC).
If you want to keep your statistics up to date, setup ``cron`` to run this
command a short time after midnight (UTC) daily.


Managing the blacklist
-----------------------------

To manage the blacklist (add, remote, list), run:

    python manage.py blacklist

Django Builtin-in Error Emails
==============================

If you'd like Django's `Builtin Email Error Reporting`_ to function properly
(actually send working emails), you'll have to explicitly set the
``SERVER_EMAIL`` setting to one of your SES-verified addresses. Otherwise, your
error emails will all fail and you'll be blissfully unaware of a problem.

*Note:* You will need to sign up for SES_ and verify any emails you're going
to use in the `from_email` argument to `django.core.mail.send_email()`. Boto_
has a `verify_email_address()` method: https://github.com/boto/boto/blob/master/boto/ses/connection.py

.. _Boto: http://boto.cloudhackers.com/
.. _Builtin Email Error Reporting: https://docs.djangoproject.com/en/dev/howto/error-reporting/


Receiving emails
================

In order to setup your AWS SES account to receive emails you should follow the
official `SES Email receiving setup`_ instructions. Here is a quick sum up:

1. Add an ``MX`` entry to your domain, pointing to ``inbound-smtp.us-east-1.amazonaws.com`` (or the region of your choice).
2. Create a new rule set in the ``Email receiving`` section.
3. Create a new rule in the newly created rule set.
4. Create a new recipient condition for that rule. In the ``actions`` step pick
   either ``Publish to Amazon SNS topic`` or ``Deliver to S3 bucket``. Also create
   a new SNS topic. That should point to ``https://your-django-ses-app/ses/event-webhook/``.
   Don't enable raw message delivery.

The difference between ``SNS`` and ``S3`` in the 4th step is that ``SNS`` will
deliver the entire email message (headers, subject, content and attachments)
directly to your endpoint; ``S3``, on the other hand, will store the email message
in a ``S3`` bucket and will deliver to your endpoint the bucket name and the
file path, then your webhook handler should fetch that file from the ``S3`` bucket
in order to get the actual email object.

The ``SNS`` way is easier to setup, but it only supports messages up to 150kb,
including headers.

Depending which method you selected in step 4 you should inherit either from the
``SnsHandler`` or the ``S3Handler`` class and create your own handler.
You should then set the path of your handler in the ``AWS_SES_INBOUND_HANDLER``
setting (eg. ``AWS_SES_INBOUND_HANDLER='my_app.service.MyReceiver'``).

Example

.. code-block:: python

   from django_ses.inbound import SnsHandler

   class MyReceiver(SnsHandler):
       def process(self):
           print(self.email.get("subject"))
           print(self.email.get("plain_text"))


The email parsing logic in Django-SES has been kept simple in order to avoid
extra dependencies. If you wish to parse emails yourself or with a third party
package, you can reimplement the ``parse_email`` method:

.. code-block:: python

   import mailparser
   from django_ses.inbound import

   class MyReceiver(SnsHandler):
       def parse_email(self, content):
           return mailparser.parse_from_bytes(content)

       def process(self):
           print(self.email.subject)
           print(self.email.body)


.. _SES Email receiving setup: https://docs.aws.amazon.com/ses/latest/dg/receiving-email-setting-up.html

Requirements
============
django-ses requires supported version of Django or Python.


Full List of Settings
=====================

``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``
  *Required.* Your API keys for Amazon SES.

``AWS_SES_ACCESS_KEY_ID``, ``AWS_SES_SECRET_ACCESS_KEY``
  *Required.* Alternative API keys for Amazon SES. This is useful in situations
  where you would like to use separate access keys for different AWS services.

``AWS_SES_SESSION_TOKEN``, ``AWS_SES_SECRET_ACCESS_KEY``
  Optional. Use `AWS_SES_SESSION_TOKEN` to provide session token
  when temporary credentials are used. Details:
  https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html
  https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_use-resources.html

``AWS_SES_REGION_NAME``, ``AWS_SES_REGION_ENDPOINT``
  Optionally specify what region your SES service is using. Note that this is
  required if your SES service is not using us-east-1, as omitting these settings
  implies this region. Details:
  http://readthedocs.org/docs/boto/en/latest/ref/ses.html#boto.ses.regions
  http://docs.aws.amazon.com/general/latest/gr/rande.html

``USE_SES_V2``
  Optional. If you want to use client v2, you'll need to add `USE_SES_V2=True`.
  Some settings will need this flag enabled.
  See https://boto3.amazonaws.com/v1/documentation/api/1.26.31/reference/services/sesv2.html#id87

``AWS_SES_FROM_EMAIL``
  Optional. The email address to be used as the "From" address for the email. The address that you specify has to be verified.
  For more information please refer to https://boto3.amazonaws.com/v1/documentation/api/1.26.31/reference/services/sesv2.html#SESV2.Client.send_email

``AWS_SES_RETURN_PATH``
  Optional. Use `AWS_SES_RETURN_PATH` to receive complaint notifications
  You must use the v2 client by setting `USE_SES_V2=True` for this setting to work, otherwise it is ignored.
  https://docs.aws.amazon.com/ses/latest/APIReference-V2/API_SendEmail.html#API_SendEmail_RequestSyntax

``AWS_SES_CONFIGURATION_SET``
  Optional. Use this to mark your e-mails as from being from a particular SES
  Configuration Set. Set this to a string if you want all messages to have the
  same configuration set.  Set this to a callable if you want to set
  configuration set on a per message basis.

``TIME_ZONE``
  Default Django setting, optionally set this. Details:
  https://docs.djangoproject.com/en/dev/ref/settings/#time-zone

``DKIM_DOMAIN``, ``DKIM_PRIVATE_KEY``
  Optional. If these settings are defined and the pydkim_ module is installed
  then email messages will be signed with the specified key.   You will also
  need to publish your public key on DNS; the selector is set to ``ses`` by
  default.  See http://dkim.org/ for further detail.

``AWS_SES_SOURCE_ARN``
  Instruct Amazon SES to use a domain from another account.
  For more information please refer to https://docs.aws.amazon.com/ses/latest/DeveloperGuide/sending-authorization-delegate-sender-tasks-email.html

``AWS_SES_FROM_ARN``
  Instruct Amazon SES to use a domain from another account.
  For more information please refer to https://docs.aws.amazon.com/ses/latest/DeveloperGuide/sending-authorization-delegate-sender-tasks-email.html

``AWS_SES_RETURN_PATH_ARN``
  Instruct Amazon SES to use a domain from another account.
  For more information please refer to https://docs.aws.amazon.com/ses/latest/DeveloperGuide/sending-authorization-delegate-sender-tasks-email.html

``AWS_SES_VERIFY_EVENT_SIGNATURES``, ``AWS_SES_VERIFY_BOUNCE_SIGNATURES``
  Optional. Default is True. Verify the contents of the message by matching the signature
  you recreated from the message contents with the signature that Amazon SNS sent with the message.
  See https://docs.aws.amazon.com/sns/latest/dg/sns-verify-signature-of-message.html for further detail.

``EVENT_CERT_DOMAINS``, ``BOUNCE_CERT_DOMAINS``
  Optional. Default is 'amazonaws.com' and 'amazon.com'.

``AWS_SES_ADD_BOUNCE_TO_BLACKLIST``
  If set to ``True`` (default ``False``) email addresses that triggered an
  irrecoverable bounce (status in the ``5xx`` range) will be added to the
  blacklist. Note that emails will be stored in lowercase.

``AWS_SES_ADD_COMPLAINT_TO_BLACKLIST``
  If set to ``True`` (default ``False``) email addresses that triggered a complaint
  will be added to the blacklist. Note that emails will be stored in lowercase.

``AWS_SES_USE_BLACKLIST``
  If set to ``True`` (default ``False``), calls to the ``send_mail()`` method will
  cause the recipients to be filtered using the blacklist. Any recipient that
  exists in the blacklist will be removed from the email.
  You must add ``django-ses`` to ``INSTALLED_APPS`` and run migrations to get
  the database models required for this feature.

``AWS_SES_INBOUND_ACCESS_KEY_ID``
  If you're inheriting from the ``S3Handler``, you should set this so that
  Django-SES can fetch the actual email message. Make sure to attach the right
  permission policies to the IAM.

``AWS_SES_INBOUND_SECRET_ACCESS_KEY``
  Check ``AWS_SES_INBOUND_ACCESS_KEY_ID``.

``AWS_SES_INBOUND_HANDLER``
  If you want to receive emails with Django-SES, set this to the path where your
  handler is (eg ``my_app.service.MyReceiver``).

.. _pydkim: http://hewgill.com/pydkim/

Proxy
=====

If you are using a proxy, please enable it via the env variables.

If your proxy server does not have a password try the following:

.. code-block:: python

   import os
   os.environ["HTTP_PROXY"] = "http://proxy.com:port"
   os.environ["HTTPS_PROXY"] = "https://proxy.com:port"

if your proxy server has a password try the following:

.. code-block:: python

   import os
   os.environ["HTTP_PROXY"] = "http://user:password@proxy.com:port"
   os.environ["HTTPS_PROXY"] = "https://user:password@proxy.com:port"

Source: https://stackoverflow.com/a/33501223/1331671

Contributing
============
If you'd like to fix a bug, add a feature, etc

#. Start by opening an issue.
    Be explicit so that project collaborators can understand and reproduce the
    issue, or decide whether the feature falls within the project's goals.
    Code examples can be useful, too.

#. File a pull request.
    You may write a prototype or suggested fix.

#. Check your code for errors, complaints.
    Use `check.py <https://github.com/jbalogh/check>`_

#. Write and run tests.
    Write your own test showing the issue has been resolved, or the feature
    works as intended.

Git hooks (via pre-commit)
==========================

We use pre-push hooks to ensure that only linted code reaches our remote repository and pipelines aren't triggered in
vain.

To enable the configured pre-push hooks, you need to [install](https://pre-commit.com/) pre-commit and run once::

    pre-commit install -t pre-push -t pre-commit --install-hooks

This will permanently install the git hooks for both, frontend and backend, in your local
[`.git/hooks`](./.git/hooks) folder.
The hooks are configured in the [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

You can check whether hooks work as intended using the [run](https://pre-commit.com/#pre-commit-run) command::

    pre-commit run [hook-id] [options]

Example: run single hook::

    pre-commit run ruff --all-files --hook-stage push

Example: run all hooks of pre-push stage::

    pre-commit run --all-files --hook-stage push

Running Tests
=============
To run the tests::

    python runtests.py

If you want to debug the tests, just add this file as a python script to your IDE run configuration.

Creating a Release
==================

To create a release:

* Run ``poetry version {patch|minor|major}`` as explained in `the docs <https://python-poetry.org/docs/cli/#version>`_. This will update the version in pyproject.toml.
* Commit that change and use git to tag that commit with a version that matches the pattern ``v*.*.*``.
* Push the tag and the commit (note some IDEs don't push tags by default).


.. |pypi| image:: https://badge.fury.io/py/django-ses.svg
    :target: http://badge.fury.io/py/django-ses
.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/django-ses?style=flat
    :target: https://pypi.org/project/django-ses/
.. |build| image:: https://github.com/django-ses/django-ses/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/django-ses/django-ses/actions/workflows/ci.yml
.. |python| image:: https://img.shields.io/badge/python-3.8|3.9|3.10|3.11|3.12-blue.svg
    :target: https://pypi.org/project/django-ses/
.. |django| image:: https://img.shields.io/badge/django-4.2%7C%205.0+-blue.svg
    :target: https://www.djangoproject.com/

