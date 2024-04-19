from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from django_ses.views import SESEventWebhookView
from example import views

admin.autodiscover()

urlpatterns = [
    '',
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', include(admin.site.urls)),

    path('', views.index, name='index'),
    path('send-email/', views.send_email, name='send-email'),
    path('reporting/', include('django_ses.urls')),

    path('bounce/', 'django_ses.views.handle_bounce', name='handle_bounce'),  # Deprecated, see SESEventWebhookView
    path('event-webhook/', SESEventWebhookView.as_view(), name='event_webhook'),
]

urlpatterns += staticfiles_urlpatterns()
