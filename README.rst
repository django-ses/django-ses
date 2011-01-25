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
