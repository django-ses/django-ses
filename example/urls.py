try:
    from django.conf.urls import *
except ImportError: # django < 1.4
    from django.conf.urls.defaults import *

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'views.index', name='index'),
    url(r'^send-email/$', 'views.send_email', name='send-email'),
    url(r'^reporting/', include('django_ses.urls')),

    url(r'^bounce/', 'django_ses.views.handle_bounce', name='handle_bounce'),
)

urlpatterns += staticfiles_urlpatterns()
