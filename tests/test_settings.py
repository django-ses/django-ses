from django.conf import settings
from django.test import TestCase

from tests.utils import unload_django_ses


class SettingsImportTest(TestCase):
    def test_aws_access_key_given(self):
        settings.AWS_ACCESS_KEY_ID = "Yjc4MzQ4MGYzMTBhOWY3ODJhODhmNTBkN2QwY2IyZTdhZmU1NDM1ZQo"
        settings.AWS_SECRET_ACCESS_KEY = "NTBjYzAzNzVlMTA0N2FiMmFlODlhYjY5OTYwZjNkNjZmMWNhNzRhOQo"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.ACCESS_KEY, settings.AWS_ACCESS_KEY_ID)
        self.assertEqual(django_ses.settings.SECRET_KEY, settings.AWS_SECRET_ACCESS_KEY)

    def test_ses_access_key_given(self):
        settings.AWS_SES_ACCESS_KEY_ID = "YmM2M2QwZTE3ODk3NTJmYzZlZDc1MDY0ZmJkMDZjZjhmOTU0MWQ4MAo"
        settings.AWS_SES_SECRET_ACCESS_KEY = "NDNiMzRjNzlmZGU0ZDAzZTQxNTkwNzdkNWE5Y2JlNjk4OGFkM2UyZQo"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.ACCESS_KEY, settings.AWS_SES_ACCESS_KEY_ID)
        self.assertEqual(django_ses.settings.SECRET_KEY, settings.AWS_SES_SECRET_ACCESS_KEY)

    def test_aws_session_token_given(self):
        settings.AWS_SESSION_TOKEN = "FwoGZXIvYXdzED8aDAILqEtZvcDCx+KsFCK1AUwcLbm4d+mAlRWYN+r1adKoIfw"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.SESSION_TOKEN, settings.AWS_SESSION_TOKEN)

    def test_ses_session_token_given(self):
        settings.AWS_SES_SESSION_TOKEN = "jQYyLYI7nmsYjpQa2aynxovr7rwKrj71PQstMbK2oKwaT1FzasM0hjs+C5uLh"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.SESSION_TOKEN, settings.AWS_SES_SESSION_TOKEN)

    def test_ses_configuration_set_given(self):
        settings.AWS_SES_CONFIGURATION_SET = "test-set"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.AWS_SES_CONFIGURATION_SET, settings.AWS_SES_CONFIGURATION_SET)

    def test_ses_region_to_endpoint_default_given(self):
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.AWS_SES_REGION_NAME, 'us-east-1')
        self.assertEqual(django_ses.settings.AWS_SES_REGION_ENDPOINT,
                         f'email.{django_ses.settings.AWS_SES_REGION_NAME}.amazonaws.com')

    def test_ses_region_to_endpoint_set_given(self):
        settings.AWS_SES_REGION_NAME = 'eu-west-1'
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.AWS_SES_REGION_NAME, 'eu-west-1')
        self.assertEqual(django_ses.settings.AWS_SES_REGION_ENDPOINT, 'email.eu-west-1.amazonaws.com')
