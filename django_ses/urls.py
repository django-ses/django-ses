try:
    from django.conf.urls import url
except ImportError:  # django < 1.4
    from django.conf.urls.defaults import url

from django_ses.views import dashboard

urlpatterns = [
    url(r'^$', dashboard, name='django_ses_stats'),
]
