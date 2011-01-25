from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'views.email_form', name='email-form'),
    url(r'^send-email/$', 'views.send_email', name='send-email'),
)
