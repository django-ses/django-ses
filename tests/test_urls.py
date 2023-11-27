from django.urls import re_path

from django_ses.views import DashboardView, SESEventWebhookView, handle_bounce

urlpatterns = [
    re_path(r'^dashboard/$', DashboardView.as_view(), name='django_ses_stats'),
    re_path(r'^bounce/$', handle_bounce, name='django_ses_bounce'),
    re_path(r'^event-webhook/$', SESEventWebhookView.as_view(), name='event_webhook'),
]
