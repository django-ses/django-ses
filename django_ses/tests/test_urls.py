try:
    from django.conf.urls import url
except ImportError:
    # Fall back to the old, pre-1.6 style
    from django.conf.urls.defaults import url

from django_ses.views import dashboard, handle_bounce

urlpatterns = [
    url(r'^dashboard/$', dashboard, name='django_ses_stats'),
    url(r'^bounce/$', handle_bounce, name='django_ses_bounce'),
    #url(r'^complaint/$', 'handle_complaint', name='django_ses_complaint'),
]
