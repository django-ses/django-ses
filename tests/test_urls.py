from django.conf.urls import url

from django_ses.views import DashboardView, handle_bounce, SESEventWebhookView

urlpatterns = [
    url(r'^dashboard/$', DashboardView.as_view(), name='django_ses_stats'),
    url(r'^bounce/$', handle_bounce, name='django_ses_bounce'),
    url(r'^event-webhook/$', SESEventWebhookView.as_view(), name='event_webhook'),
]
