from django.conf.urls import url

from django_ses.views import dashboard, handle_bounce, handle_event

urlpatterns = [
    url(r'^dashboard/$', dashboard, name='django_ses_stats'),
    url(r'^bounce/$', handle_bounce, name='django_ses_bounce'),
    url(r'^event/$', handle_event, name='django_ses_event'),
]
