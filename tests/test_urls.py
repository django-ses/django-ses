from django.urls import path

from django_ses.views import DashboardView, SESEventWebhookView, handle_bounce

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='django_ses_stats'),
    path('bounce/', handle_bounce, name='django_ses_bounce'),
    path('event-webhook/', SESEventWebhookView.as_view(), name='event_webhook'),
]
