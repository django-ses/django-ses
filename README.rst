==========
Django-SES
==========
:Info: A Django email backend for Amazon's Simple Email Service
:Author: Harry Marr (http://github.com/hmarr, http://twitter.com/harrymarr)

Getting going
=============
Assuming you've got Django installed, you'll need Boto, a Python library that
wraps the AWS API. At this stage there is no support for SES in the stable
version of Boto so you'll need to install my fork, which contains an
implementation::

    pip install -e git://github.com/hmarr/boto@ses#egg=boto

Install django-ses the same way (it'll be coming to PyPI before too long)::

    pip install -e git://github.com/hmarr/django-ses#egg=django_ses

Add the following to your settings.py::

    EMAIL_BACKEND = 'django_ses.SESBackend'

    # These are optional -- if they're set as environment variables they won't
    # need to be set here as well
    AWS_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
    AWS_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'

Now, when you use ``django.core.mail.send_mail``, Simple Email Service will
send the messages by default.

Check out the ``example`` directory for more information.

Django Builtin-in Error Emails
==============================

If you'd like Django's `Bultin Email Error Reporting`_ to function properly
(actually send working emails), you'll have to explicitly set the
``SERVER_EMAIL`` setting to one of your SES-verified addresses. Otherwise, your
error emails will all fail and you'll be blissfully unaware of a problem.

Error Handling
==============
Since other pluggable Django applications often expect SMTP exceptions when
handling email, django-ses attempts to wrap certain AWS exceptions to their
corresponding SMTP exception. This allows django-ses to be used transparently
with applications like Django-Mailer while doing the Right Thing for certain
kinds of errors.

.. _Builtin Email Error Reporting: http://docs.djangoproject.com/en/1.2/howto/error-reporting/