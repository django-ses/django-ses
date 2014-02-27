try:
    from django.conf.urls import patterns, url
except ImportError:
    # Fall back to the old, pre-1.6 style
    from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('django_ses.views',
    url(r'^dashboard/$', 'dashboard', name='django_ses_stats'),
    url(r'^bounce/$', 'handle_bounce', name='django_ses_bounce'),
    #url(r'^complaint/$', 'handle_complaint', name='django_ses_complaint'),
)
