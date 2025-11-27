from django.test import TestCase, override_settings

from django_ses import settings


class SettingsImportTest(TestCase):
    @override_settings(
        AWS_ACCESS_KEY_ID='<<access_key>>',
        AWS_SECRET_ACCESS_KEY='<<secret_key>>',
    )
    def test_aws_access_key_given(self):
        self.assertEqual(settings.ACCESS_KEY, '<<access_key>>')
        self.assertEqual(settings.SECRET_KEY, '<<secret_key>>')

    @override_settings(
        AWS_SES_ACCESS_KEY_ID='<<access_key>>',
        AWS_SES_SECRET_ACCESS_KEY='<<secret_key>>',
    )
    def test_ses_access_key_given(self):
        self.assertEqual(settings.ACCESS_KEY, '<<access_key>>')
        self.assertEqual(settings.SECRET_KEY, '<<secret_key>>')

    @override_settings(AWS_SESSION_TOKEN='<<session_token>>')
    def test_aws_session_token_given(self):
        self.assertEqual(settings.SESSION_TOKEN, '<<session_token>>')

    @override_settings(AWS_SES_SESSION_TOKEN='<<session_token>>')
    def test_ses_session_token_given(self):
        self.assertEqual(settings.SESSION_TOKEN, '<<session_token>>')

    @override_settings(AWS_SES_CONFIGURATION_SET='<<config_set>>')
    def test_ses_configuration_set_given(self):
        self.assertEqual(settings.AWS_SES_CONFIGURATION_SET, '<<config_set>>')

    def test_ses_region_to_endpoint_default_given(self):
        self.assertEqual(settings.AWS_SES_REGION_NAME, 'us-east-1')
        self.assertEqual(
            settings.AWS_SES_REGION_ENDPOINT,
            f'email.{settings.AWS_SES_REGION_NAME}.amazonaws.com',
        )

    @override_settings(AWS_SES_REGION_NAME='eu-west-1')
    def test_ses_region_to_endpoint_set_given(self):
        self.assertEqual(settings.AWS_SES_REGION_NAME, 'eu-west-1')
        self.assertEqual(settings.AWS_SES_REGION_ENDPOINT, 'email.eu-west-1.amazonaws.com')
