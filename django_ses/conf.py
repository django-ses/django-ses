from typing import List, Optional

from django.conf import settings as django_settings

# Allow uppercase variable names for settings properties
# ruff: noqa: N802


class SesSettings:
    @property
    def AWS_SESSION_PROFILE(self) -> Optional[str]:
        return getattr(django_settings, 'AWS_SESSION_PROFILE', None)

    @property
    def ACCESS_KEY(self) -> Optional[str]:
        return getattr(
            django_settings,
            'AWS_SES_ACCESS_KEY_ID',
            getattr(django_settings, 'AWS_ACCESS_KEY_ID', None),
        )

    @property
    def SECRET_KEY(self) -> Optional[str]:
        return getattr(
            django_settings,
            'AWS_SES_SECRET_ACCESS_KEY',
            getattr(django_settings, 'AWS_SECRET_ACCESS_KEY', None),
        )

    @property
    def SESSION_TOKEN(self) -> Optional[str]:
        return getattr(
            django_settings,
            'AWS_SES_SESSION_TOKEN',
            getattr(django_settings, 'AWS_SESSION_TOKEN', None),
        )

    @property
    def AWS_SES_REGION_NAME(self) -> str:
        return getattr(
            django_settings,
            'AWS_SES_REGION_NAME',
            getattr(django_settings, 'AWS_DEFAULT_REGION', 'us-east-1'),
        )

    @property
    def AWS_SES_REGION_ENDPOINT(self) -> str:
        return getattr(django_settings, 'AWS_SES_REGION_ENDPOINT', f'email.{self.AWS_SES_REGION_NAME}.amazonaws.com')

    @property
    def AWS_SES_REGION_ENDPOINT_URL(self) -> str:
        return getattr(django_settings, 'AWS_SES_REGION_ENDPOINT_URL', 'https://' + self.AWS_SES_REGION_ENDPOINT)

    @property
    def AWS_SES_AUTO_THROTTLE(self) -> float:
        return getattr(django_settings, 'AWS_SES_AUTO_THROTTLE', 0.5)

    @property
    def AWS_SES_CONFIG(self):
        return getattr(django_settings, 'AWS_SES_CONFIG', None)

    @property
    def AWS_SES_RETURN_PATH(self) -> Optional[str]:
        return getattr(django_settings, 'AWS_SES_RETURN_PATH', None)

    @property
    def AWS_SES_CONFIGURATION_SET(self) -> Optional[str]:
        return getattr(django_settings, 'AWS_SES_CONFIGURATION_SET', None)

    @property
    def DKIM_DOMAIN(self) -> Optional[str]:
        return getattr(django_settings, 'DKIM_DOMAIN', None)

    @property
    def DKIM_PRIVATE_KEY(self) -> Optional[str]:
        return getattr(django_settings, 'DKIM_PRIVATE_KEY', None)

    @property
    def DKIM_SELECTOR(self) -> str:
        return getattr(django_settings, 'DKIM_SELECTOR', 'ses')

    @property
    def DKIM_HEADERS(self) -> List[str]:
        return getattr(django_settings, 'DKIM_HEADERS', ['From', 'To', 'Cc', 'Subject'])

    @property
    def AWS_SES_SOURCE_ARN(self) -> Optional[str]:
        return getattr(django_settings, 'AWS_SES_SOURCE_ARN', None)

    @property
    def AWS_SES_FROM_ARN(self) -> Optional[str]:
        return getattr(django_settings, 'AWS_SES_FROM_ARN', None)

    @property
    def AWS_SES_RETURN_PATH_ARN(self) -> Optional[str]:
        return getattr(django_settings, 'AWS_SES_RETURN_PATH_ARN', None)

    @property
    def USE_SES_V2(self) -> bool:
        return getattr(django_settings, 'USE_SES_V2', False)

    @property
    def AWS_SES_FROM_EMAIL(self) -> Optional[str]:
        return getattr(django_settings, 'AWS_SES_FROM_EMAIL', None)

    @property
    def TIME_ZONE(self) -> str:
        return django_settings.TIME_ZONE

    @property
    def VERIFY_EVENT_SIGNATURES(self) -> bool:
        return getattr(
            django_settings,
            'AWS_SES_VERIFY_EVENT_SIGNATURES',
            getattr(django_settings, 'AWS_SES_VERIFY_BOUNCE_SIGNATURES', True),
        )

    VERIFY_BOUNCE_SIGNATURES = VERIFY_EVENT_SIGNATURES

    # Domains that are trusted when retrieving the certificate used to sign event messages.
    @property
    def EVENT_CERT_DOMAINS(self) -> List[str]:
        return getattr(
            django_settings,
            'AWS_SNS_EVENT_CERT_TRUSTED_DOMAINS',
            getattr(
                django_settings,
                'AWS_SNS_BOUNCE_CERT_TRUSTED_DOMAINS',
                [
                    'amazonaws.com',
                    'amazon.com',
                ],
            ),
        )

    BOUNCE_CERT_DOMAINS = EVENT_CERT_DOMAINS

    # Blacklists
    @property
    def AWS_SES_ADD_BOUNCE_TO_BLACKLIST(self) -> bool:
        return getattr(django_settings, 'AWS_SES_ADD_BOUNCE_TO_BLACKLIST', False)

    @property
    def AWS_SES_ADD_COMPLAINT_TO_BLACKLIST(self) -> bool:
        return getattr(django_settings, 'AWS_SES_ADD_COMPLAINT_TO_BLACKLIST', False)

    @property
    def AWS_SES_USE_BLACKLIST(self) -> bool:
        return getattr(django_settings, 'AWS_SES_USE_BLACKLIST', False)

    # Inbound
    @property
    def AWS_SES_INBOUND_HANDLER(self) -> str:
        return getattr(django_settings, 'AWS_SES_INBOUND_HANDLER', 'django_ses.inbound.raw_handler')

    # Required if the configured action is set to "Deliver to Amazon S3 bucket"
    # These credentials will be used to access the bucket where the email was stored
    @property
    def AWS_SES_INBOUND_ACCESS_KEY_ID(self) -> str:
        return getattr(django_settings, 'AWS_SES_INBOUND_ACCESS_KEY_ID', '')

    @property
    def AWS_SES_INBOUND_SECRET_ACCESS_KEY(self) -> str:
        return getattr(django_settings, 'AWS_SES_INBOUND_SECRET_ACCESS_KEY', '')

    @property
    def AWS_SES_INBOUND_SESSION_TOKEN(self) -> str:
        return getattr(django_settings, 'AWS_SES_INBOUND_SESSION_TOKEN', '')


settings = SesSettings()
