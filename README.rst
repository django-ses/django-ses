==========
Django-SES
==========
:Info: A Django email backend for Amazon's Simple Email Service
:Author: Harry Marr (http://github.com/hmarr, http://twitter.com/harrymarr)

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
Assuming you've got Django_ installed, you'll need Boto_ 2.0b4 or higher. Boto_
is a Python library that wraps the AWS API.

You can do the following to install boto 2.0b4 (we're using --upgrade here to
make sure you get 2.0b4)::

    pip install --upgrade boto

Install django-ses::

    pip install django-ses

Add the following to your settings.py::

    EMAIL_BACKEND = 'django_ses.SESBackend'

    # These are optional -- if they're set as environment variables they won't
    # need to be set here as well
    AWS_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
    AWS_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'

Now, when you use ``django.core.mail.send_mail``, Simple Email Service will
send the messages by default.

Check out the ``example`` directory for more information.

SES Stats Report
================

A very simple read-only report on your quota, verified email addresses and
sending statistics is included.

If you wish to use the SES sending statistics reports, you must include
``django_ses`` in your INSTALLED_APPS and you must include ``django_ses.urls``
in your ``urls.py``.

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
