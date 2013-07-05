try:
    from django.conf.urls import patterns, url
except ImportError: # django < 1.4
    from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('django_ses.views',
    url(r'^$', 'dashboard', name='django_ses_stats'),
)
