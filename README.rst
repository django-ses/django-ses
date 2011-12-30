==========
Django-SES
==========
:Info: A Django email backend for Amazon's Simple Email Service
:Author: Harry Marr (http://github.com/hmarr, http://twitter.com/harrymarr)
:Collaborator: Paul Craciunoiu (http://github.com/pcraciunoiu, http://twitter.com/embrangler)

A bird's eye view
=================
Django-SES is a drop-in mail backend for Django_. Instead of sending emails
through a traditional SMTP mail server, Django-SES routes email through
Amazon Web Services' excellent Simple Email Service (SES_).

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

    # Additionally, you can specify an optional region, like so:
    AWS_SES_REGION_NAME = 'us-east-1'
    AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'

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

SES Stats Report
================

A very simple read-only report on your quota, verified email addresses and
sending statistics is included.

If you wish to use the SES sending statistics reports, you must include
``django.contrib.admin``(for templates) and ``django_ses`` in your 
INSTALLED_APPSand you must include ``django_ses.urls`` in your ``urls.py``.

Additionally, you can install ``pytz`` to localize the Amazon timestamp 
(assumed UTC) to your locale. This will also make the date more readable,
using Django's default formatting.

Django Management Command
=========================

Manage verified email addresses through the management command.

``./manage.py ses_email_address -l``

To use you must include ``django_ses`` in your INSTALLED_APPS.

Django Builtin-in Error Emails
==============================

If you'd like Django's `Builtin Email Error Reporting`_ to function properly
(actually send working emails), you'll have to explicitly set the
``SERVER_EMAIL`` setting to one of your SES-verified addresses. Otherwise, your
error emails will all fail and you'll be blissfully unaware of a problem.

*Note:* You will need to sign up for SES_ and verify any emails you're going
to use in the `from_email` argument to `django.core.mail.send_email()`. Boto_
has a `verify_email_address()` method: https://github.com/boto/boto/blob/master/boto/ses/connection.py

.. _Builtin Email Error Reporting: http://docs.djangoproject.com/en/1.2/howto/error-reporting/
.. _Django: http://djangoproject.com
.. _Boto: http://boto.cloudhackers.com/
.. _SES: http://aws.amazon.com/ses/

Requirements
============
django-ses requires boto version 2.1.0 or later.

Full List of Settings
=====================

``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``
  *Required.* Your API keys from Amazon SES.

``AWS_SES_REGION_NAME``, ``AWS_SES_REGION_ENDPOINT``
  Optionally specify what region your SES service is using. Details:
  http://readthedocs.org/docs/boto/en/latest/ref/ses.html#boto.ses.regions

``AWS_SES_RETURN_PATH``
  Instruct Amazon SES to forward bounced emails and complaints to this email.
  For more information please refer to http://aws.amazon.com/ses/faqs/#38

``TIME_ZONE``
  Default Django setting, optionally set this. Details:
  https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
