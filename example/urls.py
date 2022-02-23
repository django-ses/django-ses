from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, re_path

from django_ses.views import SESEventWebhookView
from example import views

admin.autodiscover()

urlpatterns = [
    '',
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', include(admin.site.urls)),

    re_path(r'^$', views.index, name='index'),
    re_path(r'^send-email/$', views.send_email, name='send-email'),
    re_path(r'^reporting/', include('django_ses.urls')),

    re_path(r'^bounce/', 'django_ses.views.handle_bounce', name='handle_bounce'),       # Deprecated, see SESEventWebhookView.
    re_path(r'^event-webhook/', SESEventWebhookView.as_view(), name='event_webhook'),
]

urlpatterns += staticfiles_urlpatterns()
