==========
Django-SES
==========
:Info: A Django email backend for Amazon's Simple Email Service
:Author: Harry Marr (http://github.com/hmarr, http://twitter.com/harrymarr)
:Collaborators: Paul Craciunoiu (http://github.com/pcraciunoiu, http://twitter.com/embrangler)

.. image:: https://travis-ci.org/django-ses/django-ses.svg
    :target: https://travis-ci.org/django-ses/django-ses

A bird's eye view
=================
Django-SES is a drop-in mail backend for Django_. Instead of sending emails
through a traditional SMTP mail server, Django-SES routes email through
Amazon Web Services' excellent Simple Email Service (SES_).


Using Django directly
=====================

Amazon SES allows you to also setup usernames and passwords. If you do configure
things that way, you do not need this package. The Django default email backend
is capable of authenticating with Amazon SES and correctly sending email.

Using django-ses gives you additional features like deliverability reports that
can be hard and/or cumbersome to obtain when using the SMTP interface.

**Note:** In order to use smtp with Amazon SES, you may have to install some
supporting packages for ssl. Check out `this SMTP SSL email backend for Django`__

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

Getting going
=============
Assuming you've got Django_ installed, you'll need Boto_ 2.1.0 or higher. Boto_
is a Python library that wraps the AWS API.

You can do the following to install boto 2.1.0 (we're using --upgrade here to
make sure you get 2.1.0)::

    pip install --upgrade boto

Install django-ses::

    pip install django-ses

Add the following to your settings.py::

    EMAIL_BACKEND = 'django_ses.SESBackend'

    # These are optional -- if they're set as environment variables they won't
    # need to be set here as well
    AWS_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
    AWS_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'

    # Additionally, if you are not using the default AWS region of us-east-1,
    # you need to specify a region, like so:
    AWS_SES_REGION_NAME = 'us-west-2'
    AWS_SES_REGION_ENDPOINT = 'email.us-west-2.amazonaws.com'

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
To set this up, install `django-ses` with the `bounce` extra::

    pip install django-ses[bounce]

Then add a bounce url handler in your `urls.py`, create Topics and configure
Subscription in Amazon::

    from django_ses.views import handle_bounce
    from django.views.decorators.csrf import csrf_exempt
    urlpatterns = [ ...
                    url(r'^ses/bounce/$', csrf_exempt(handle_bounce)),
                    ...
    ]

Amazon SNS has three signals for each status (bounce, complaint, delivery).

Bounces
-------
Using signal 'bounce_received' for manager bounce email. For example::

    from django_ses.signals import bounce_received
    from django.dispatch import receiver


    @receiver(bounce_received)
    def bounce_handler(sender, *args, **kwargs):
        print("This is bounce email object")
        print(kwargs.get('mail_obj'))

Complaint
---------
Using signal 'complaint_received' for manager complaint email. For example::

    from django_ses.signals import complaint_received
    from django.dispatch import receiver


    @receiver(complaint_received)
    def complaint_handler(sender, *args, **kwargs):
        print("This is complaint email object")
        print(kwargs.get('mail_obj'))

Delivery
--------
Using signal 'delivery_received' for manager delivery email. For example::

    from django_ses.signals import delivery_received
    from django.dispatch import receiver


    @receiver(delivery_received)
    def delivery_handler(sender, *args, **kwargs):
        print("This is delivery email object")
        print(kwargs.get('mail_obj'))

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


SES Sending Stats
=================

Django SES comes with two ways of viewing sending statistics.

The first one is a simple read-only report on your 24 hour sending quota,
verified email addresses and bi-weekly sending statistics.

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


Link the dashboard from the admin
---------------------------------
You can use adminplus for this (https://github.com/jsocol/django-adminplus)::

    from django_ses.views import dashboard
    admin.site.register_view('django-ses', dashboard, 'Django SES Stats')

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

    python manage.py ses_email_address -l


Collecting Sending Statistics
-----------------------------

To collect and store SES sending statistics in the database, run:

    python manage.py get_ses_statistics

Sending statistics are aggregated daily (UTC time). Stats for the latest day
(when you run the command) may be inaccurate if run before end of day (UTC).
If you want to keep your statistics up to date, setup ``cron`` to run this
command a short time after midnight (UTC) daily.


Django Builtin-in Error Emails
==============================

If you'd like Django's `Builtin Email Error Reporting`_ to function properly
(actually send working emails), you'll have to explicitly set the
``SERVER_EMAIL`` setting to one of your SES-verified addresses. Otherwise, your
error emails will all fail and you'll be blissfully unaware of a problem.

*Note:* You will need to sign up for SES_ and verify any emails you're going
to use in the `from_email` argument to `django.core.mail.send_email()`. Boto_
has a `verify_email_address()` method: https://github.com/boto/boto/blob/master/boto/ses/connection.py

.. _Builtin Email Error Reporting: https://docs.djangoproject.com/en/dev/howto/error-reporting/
.. _Django: http://djangoproject.com
.. _Boto: http://boto.cloudhackers.com/
.. _SES: http://aws.amazon.com/ses/
.. _SES Event Publishing: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/monitor-using-event-publishing.html
__ https://github.com/bancek/django-smtp-ssl

Requirements
============
django-ses requires boto version 2.1.0 or later.

Full List of Settings
=====================

``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``
  *Required.* Your API keys for Amazon SES.

``AWS_SES_ACCESS_KEY_ID``, ``AWS_SES_SECRET_ACCESS_KEY``
  *Required.* Alternative API keys for Amazon SES. This is useful in situations
  where you would like to use separate access keys for different AWS services.

``AWS_SES_REGION_NAME``, ``AWS_SES_REGION_ENDPOINT``
  Optionally specify what region your SES service is using. Note that this is
  required if your SES service is not using us-east-1, as omitting these settings
  implies this region. Details:
  http://readthedocs.org/docs/boto/en/latest/ref/ses.html#boto.ses.regions
  http://docs.aws.amazon.com/general/latest/gr/rande.html

``AWS_SES_RETURN_PATH``
  Instruct Amazon SES to forward bounced emails and complaints to this email.
  For more information please refer to http://aws.amazon.com/ses/faqs/#38

``AWS_SES_CONFIGURATION_SET``
  Optional. Use this to mark your e-mails as from being from a particular SES
  Configuration Set. Set this to a string if you want all messages to have the
  same configuration set.  Set this to a callable if you want to set
  configuration set on a per message basis.

``AWS_SES_PROXY``
  Optional. Use this address as a proxy while connecting to Amazon SES.

``AWS_SES_PROXY_PORT``
  Optional. Use this port for proxy connections while connecting to Amazon SES.

``AWS_SES_PROXY_USER``
  Optional. Use this user when setting up proxy connections while connecting to Amazon SES.

``AWS_SES_PROXY_PASS``
  Optional. Use this password when setting up proxy connections while connecting to Amazon SES.


``TIME_ZONE``
  Default Django setting, optionally set this. Details:
  https://docs.djangoproject.com/en/dev/ref/settings/#time-zone

``DKIM_DOMAIN``, ``DKIM_PRIVATE_KEY``
  Optional. If these settings are defined and the pydkim_ module is installed
  then email messages will be signed with the specified key.   You will also
  need to publish your public key on DNS; the selector is set to ``ses`` by
  default.  See http://dkim.org/ for further detail.

.. _pydkim: http://hewgill.com/pydkim/

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

Running Tests
=============
To run the tests::

    python manage.py test django_ses

Creating a Release
==================

To create a release::

    virtualenv -p python3 ~/.virtualenvs/django-ses
    workon django-ses
    pip3 install twine
    python3 setup.py sdist
    python3 setup.py bdist_wheel --universal
    twine upload dist/*
