from django.urls import path

from django_ses.views import dashboard


urlpatterns = [
    path('', dashboard, name='django_ses_stats'),
]
