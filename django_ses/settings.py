from django.conf import settings
from boto.ses import SESConnection

__all__ = ('ACCESS_KEY', 'SECRET_KEY', 'AWS_SES_REGION_NAME',
        'AWS_SES_REGION_ENDPOINT', 'AWS_SES_AUTO_THROTTLE',
        'AWS_SES_RETURN_PATH', 'DKIM_DOMAIN', 'DKIM_PRIVATE_KEY',
        'DKIM_SELECTOR', 'DKIM_HEADERS', 'TIME_ZONE')

ACCESS_KEY = getattr(settings, 'AWS_SES_ACCESS_KEY_ID',
    getattr(settings, 'AWS_ACCESS_KEY_ID', None))

SECRET_KEY = getattr(settings, 'AWS_SES_SECRET_ACCESS_KEY',
    getattr(settings, 'AWS_SECRET_ACCESS_KEY', None))

AWS_SES_REGION_NAME = getattr(settings, 'AWS_SES_REGION_NAME',
    SESConnection.DefaultRegionName),
AWS_SES_REGION_ENDPOINT = getattr(settings, 'AWS_SES_REGION_ENDPOINT',
    SESConnection.DefaultRegionEndpoint)

AWS_SES_AUTO_THROTTLE = getattr(settings, 'AWS_SES_AUTO_THROTTLE', 0.5)
AWS_SES_RETURN_PATH = getattr(settings, 'AWS_SES_RETURN_PATH', None)

DKIM_DOMAIN = getattr(settings, "DKIM_DOMAIN", None)
DKIM_PRIVATE_KEY = getattr(settings, 'DKIM_PRIVATE_KEY', None)
DKIM_SELECTOR = getattr(settings, 'DKIM_SELECTOR', 'ses')
DKIM_HEADERS = getattr(settings, 'DKIM_HEADERS',
                        ('From', 'To', 'Cc', 'Subject'))

TIME_ZONE = settings.TIME_ZONE
