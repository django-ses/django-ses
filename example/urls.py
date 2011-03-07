from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'views.index', name='index'),
    url(r'^send-email/$', 'views.send_email', name='send-email'),
    url(r'^reporting/', include('django_ses.urls')),
)
