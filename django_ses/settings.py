from django.conf import settings

__all__ = ('AWS_SESSION_PROFILE','ACCESS_KEY', 'SECRET_KEY', 'AWS_SES_REGION_NAME',
           'AWS_SES_REGION_ENDPOINT', 'AWS_SES_AUTO_THROTTLE',
           'AWS_SES_CONFIG',  'AWS_SES_RETURN_PATH',
           'DKIM_DOMAIN', 'DKIM_PRIVATE_KEY',
           'DKIM_SELECTOR', 'DKIM_HEADERS', 'TIME_ZONE')

AWS_SESSION_PROFILE = getattr(settings, "AWS_SESSION_PROFILE", None)
ACCESS_KEY = getattr(settings, 'AWS_SES_ACCESS_KEY_ID',
                     getattr(settings, 'AWS_ACCESS_KEY_ID', None))

SECRET_KEY = getattr(settings, 'AWS_SES_SECRET_ACCESS_KEY',
                     getattr(settings, 'AWS_SECRET_ACCESS_KEY', None))

SESSION_TOKEN = getattr(settings, 'AWS_SES_SESSION_TOKEN',
                     getattr(settings, 'AWS_SESSION_TOKEN', None))

AWS_SES_REGION_NAME = getattr(settings, 'AWS_SES_REGION_NAME',
                              getattr(settings, 'AWS_DEFAULT_REGION', 'us-east-1'))
AWS_SES_REGION_ENDPOINT = getattr(settings, 'AWS_SES_REGION_ENDPOINT',
                                  f'email.{AWS_SES_REGION_NAME}.amazonaws.com')
AWS_SES_REGION_ENDPOINT_URL = getattr(settings, 'AWS_SES_REGION_ENDPOINT_URL',
                                      'https://' + AWS_SES_REGION_ENDPOINT)

AWS_SES_AUTO_THROTTLE = getattr(settings, 'AWS_SES_AUTO_THROTTLE', 0.5)
AWS_SES_CONFIG = getattr(settings, 'AWS_SES_CONFIG', None)
AWS_SES_RETURN_PATH = getattr(settings, 'AWS_SES_RETURN_PATH', None)
AWS_SES_CONFIGURATION_SET = getattr(settings, 'AWS_SES_CONFIGURATION_SET', None)

DKIM_DOMAIN = getattr(settings, "DKIM_DOMAIN", None)
DKIM_PRIVATE_KEY = getattr(settings, 'DKIM_PRIVATE_KEY', None)
DKIM_SELECTOR = getattr(settings, 'DKIM_SELECTOR', 'ses')
DKIM_HEADERS = getattr(settings, 'DKIM_HEADERS',
                       ('From', 'To', 'Cc', 'Subject'))

AWS_SES_SOURCE_ARN = getattr(settings, 'AWS_SES_SOURCE_ARN', None)
AWS_SES_FROM_ARN = getattr(settings, 'AWS_SES_FROM_ARN', None)
AWS_SES_RETURN_PATH_ARN = getattr(settings, 'AWS_SES_RETURN_PATH_ARN', None)

USE_SES_V2 = getattr(settings, 'USE_SES_V2', False)
AWS_SES_FROM_EMAIL = getattr(settings, 'AWS_SES_FROM_EMAIL', None)

TIME_ZONE = settings.TIME_ZONE

VERIFY_EVENT_SIGNATURES = getattr(settings, 'AWS_SES_VERIFY_EVENT_SIGNATURES',
                                  getattr(settings, 'AWS_SES_VERIFY_BOUNCE_SIGNATURES', True))
VERIFY_BOUNCE_SIGNATURES = VERIFY_EVENT_SIGNATURES

# Domains that are trusted when retrieving the certificate used to sign event messages.
EVENT_CERT_DOMAINS = getattr(
    settings,
    'AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS',
    getattr(
        settings,
        'AWS_SNS_BOUNCE_CERT_TRUSTED_DOMAINS',
        (
            'amazonaws.com',
            'amazon.com',
        )
    )
)
BOUNCE_CERT_DOMAINS = EVENT_CERT_DOMAINS

# Blacklists
AWS_SES_ADD_BOUNCE_TO_BLACKLIST = getattr(settings, 'AWS_SES_ADD_BOUNCE_TO_BLACKLIST', False)
AWS_SES_ADD_COMPLAINT_TO_BLACKLIST = getattr(settings, 'AWS_SES_ADD_COMPLAINT_TO_BLACKLIST', False)
AWS_SES_USE_BLACKLIST = getattr(settings, 'AWS_SES_USE_BLACKLIST', False)

# Inbound
AWS_SES_INBOUND_HANDLER = getattr(settings, 'AWS_SES_INBOUND_HANDLER', 'django_ses.inbound.raw_handler')
# Required if the configured action is set to "Deliver to Amazon S3 bucket"
# These credentials will be used to access the bucket where the email was stored
AWS_SES_INBOUND_ACCESS_KEY_ID = getattr(settings, 'AWS_SES_INBOUND_ACCESS_KEY_ID', '')
AWS_SES_INBOUND_SECRET_ACCESS_KEY = getattr(settings, 'AWS_SES_INBOUND_SECRET_ACCESS_KEY', '')
AWS_SES_INBOUND_SESSION_TOKEN = getattr(settings, 'AWS_SES_INBOUND_SESSION_TOKEN', '')
