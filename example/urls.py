from django.conf.urls import url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include

from example import views

admin.autodiscover()

urlpatterns = [
    '',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', views.index, name='index'),
    url(r'^send-email/$', views.send_email, name='send-email'),
    url(r'^reporting/', include('django_ses.urls')),

    url(r'^event/', 'django_ses.views.handle_event', name='handle_event'),
]

urlpatterns += staticfiles_urlpatterns()
