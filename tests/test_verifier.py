try:
    from unittest import mock
except ImportError:
    import mock

try:
    import requests
except ImportError:
    requests = None

try:
    from cryptography import x509
except ImportError:
    x509 = None

from unittest import TestCase, skipIf

from django_ses.utils import BounceMessageVerifier, clear_cert_cache


class BounceMessageVerifierTest(TestCase):
    """
    Test for bounce message signature verification
    """

    simple_msg = {
        "Message": "Message text",
        "MessageId": "Some ID",
        "Subject": "Equity for all",
        "Timestamp": "Yesterday",
        "TopicArn": "arn:aws...",
        "Type": "Notification",
    }

    VALID_CERT = (b"-----BEGIN CERTIFICATE-----\nMIIF1zCCBL+gAwIBAgIQB9pYWG3Mi7xej22g9pobJTANBgkqhkiG9w0BAQsFADBG\n"
                  b"MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRUwEwYDVQQLEwxTZXJ2ZXIg\nQ0EgMUIxDzANBgNVBAMTBkFtYXpvb"
                  b"jAeFw0yMTA5MDcwMDAwMDBaFw0yMjA4MTcy\nMzU5NTlaMBwxGjAYBgNVBAMTEXNucy5hbWF6b25hd3MuY29tMIIBIjANBg"
                  b"kqhkiG\n9w0BAQEFAAOCAQ8AMIIBCgKCAQEAutFqueT3XgP13udzxE6UpbdjOtVO5DwoMpSM\niDNMnGzF1TYH5/R2LPUOB"
                  b"eTB0SkKnR4kpNcUZhicpGD4aKciz/GEZ6wu65xncfT9\nH/KBOQwoXYTuClHwp6fYpGzcGFaFoEYMnijL/o4qmTSd+ukglQ"
                  b"UgKpsDw4ofw6rU\nm2CttJo+GQSNQ9NfGR1h/0J+zsApkeSYrXRx5wNlu87z8os1C/6PBrUHwt3xXeaf\nXzfwut8aRRYsS"
                  b"8BySOA9DAgLfNHlfdQCjKPXKrG/ussgReyWD6n/HH+j7Uha3xos\nTzQqJifcxlTq6MxWdPR6fDaJNvqw6DOE7UjUNxHguX"
                  b"HlVfxhlQIDAQABo4IC6TCC\nAuUwHwYDVR0jBBgwFoAUWaRmBlKge5WSPKOUByeWdFv5PdAwHQYDVR0OBBYEFAqz\nC+vyo"
                  b"uneE7mWWLbi9i0UsWUbMBwGA1UdEQQVMBOCEXNucy5hbWF6b25hd3MuY29t\nMA4GA1UdDwEB/wQEAwIFoDAdBgNVHSUEFj"
                  b"AUBggrBgEFBQcDAQYIKwYBBQUHAwIw\nOwYDVR0fBDQwMjAwoC6gLIYqaHR0cDovL2NybC5zY2ExYi5hbWF6b250cnVzdC5"
                  b"j\nb20vc2NhMWIuY3JsMBMGA1UdIAQMMAowCAYGZ4EMAQIBMHUGCCsGAQUFBwEBBGkw\nZzAtBggrBgEFBQcwAYYhaHR0cD"
                  b"ovL29jc3Auc2NhMWIuYW1hem9udHJ1c3QuY29t\nMDYGCCsGAQUFBzAChipodHRwOi8vY3J0LnNjYTFiLmFtYXpvbnRydXN"
                  b"0LmNvbS9z\nY2ExYi5jcnQwDAYDVR0TAQH/BAIwADCCAX0GCisGAQQB1nkCBAIEggFtBIIBaQFn\nAHYAKXm+8J45OSHwVn"
                  b"OfY6V35b5XfZxgCvj5TV0mXCVdx4QAAAF7vfDVkQAABAMA\nRzBFAiEA2XfHuy36aqRFiaL8c3md2mH451go8707+fRE0pE"
                  b"dSRACIE/g5FXTUXUZ\nPFcmOhm9TZ+uMY1i4CIQ/CKVWln6C3t+AHYAUaOw9f0BeZxWbbg3eI8MpHrMGyfL\n956IQpoN/t"
                  b"SLBeUAAAF7vfDVjAAABAMARzBFAiBF1MhhFP0+FQt3daDFfMYoWwnr\nmuTInrjNpwfzlvQBugIhAPYadFzr+LaxSJoiZEb"
                  b"EHBvTts7bT0M3eCQONA2O7w6n\nAHUAQcjKsd8iRkoQxqE6CUKHXk4xixsD6+tLx2jwkGKWBvYAAAF7vfDVdAAABAMA\nRj"
                  b"BEAiAtPapmFAuA71ih4NoSd5hJelzAltNQpxDMcDfDyHyU8gIgWxmaa6+2KbBu\n9xdv379zvnJACFR7jc+4asl08Dn4aag"
                  b"wDQYJKoZIhvcNAQELBQADggEBAA54QX0u\noFWXfMmv02CGZv4NWo5TapyeeixQ2kKpZHRdVZjxZrw+hoF6HD7P3kGjH8zt"
                  b"yJll\ntDxB0qgMltbPhQdScwhA6iTgoaBYqEUC/VHKd4PmmPT6yIsM36NBZVmkGlzl5uNo\n/dBgBaG0SsVJnhr5zro3c2q"
                  b"uC7n6fVGEZhf/UgQwRnnvThnvbNKguglDMq4uEqv8\nnjKyleht+glkcmXO0m9qLKt6BOS0amy6U2GlAwRn0Wx02ndJtnRC"
                  b"SC6kPuRWK/SQ\nFEjB7gCK4hdKaAOuWdZpI55vF6ifOeM8toC3g7ofO8qLTnJupAG+ZitY5J3cvHWr\nHqOUdKigPDHYLRo"
                  b"=\n-----END CERTIFICATE-----\n")
    # Any changes to this message will break the signature validity test.
    valid_msg = {
        "Type": "Notification",
        "MessageId": "97903a0c-8818-5442-94b2-60b0c63d3da0",
        "TopicArn": "arn:aws:sns:us-east-1:364852123998:test-email",
        "Subject": "Amazon SES Email Event Notification",
        "Message": '{"eventType":"Complaint","complaint":{"feedbackId":"0100017fd2f87864-7f070191-4eb1-49e3-a42e-'
                   '7e996b718724-000000","complaintSubType":null,"complainedRecipients":[{"emailAddress":'
                   '"complaint@simulator.amazonses.com"}],"timestamp":"2022-03-28T23:59:33.564Z","userAgent":'
                   '"Amazon SES Mailbox Simulator","complaintFeedbackType":"abuse","arrivalDate":'
                   '"2022-03-28T23:59:33.564Z"},"mail":{"timestamp":"2022-03-28T23:59:32.804Z","source":'
                   '"jesus.islasf@alumno.buap.mx","sourceArn":"arn:aws:ses:us-east-1:364852123998:'
                   'identity/jesus.islasf@alumno.buap.mx","sendingAccountId":"364852123998","messageId":'
                   '"0100017fd2f875c4-c2929163-2767-49b1-8513-1a29e428e134-000000","destination":'
                   '["complaint@simulator.amazonses.com"],"headersTruncated":false,"headers":[{"name":"From",'
                   '"value":"jesus.islasf@alumno.buap.mx"},{"name":"To","value":"complaint@simulator.amazonses.com"},'
                   '{"name":"Subject","value":"Complaint Notification"},{"name":"MIME-Version","value":"1.0"},'
                   '{"name":"Content-Type","value":"multipart/alternative;  '
                   'boundary=\\"----=_Part_1160373_1543555432.1648511972808\\""}],"commonHeaders":{"from":'
                   '["jesus.islasf@alumno.buap.mx"],"to":["complaint@simulator.amazonses.com"],"messageId":'
                   '"0100017fd2f875c4-c2929163-2767-49b1-8513-1a29e428e134-000000","subject":'
                   '"Complaint Notification"},"tags":{"ses:operation":["SendEmail"],"ses:configuration-set":'
                   '["test-set"],"ses:source-ip":["189.203.131.80"],"ses:from-domain":["alumno.buap.mx"],'
                   '"ses:caller-identity":["root"]}}}\n',
        "Timestamp": "2022-03-28T23:59:33.713Z",
        "SignatureVersion": "1",
        "Signature": "MAnUSvI5C6S0GERh05oFiMtpZuGTW0J/6I/AaBinsZWK+Na8TwJsiNSUjShgZ8NItzQkjBnY1R1qT0wtPf6FfNXxGu3"
                     "oQRaYsj1alz5NJyiuZwGlryX9LHuOoSJ7tGhrKA5yfYI1JPZsdUJKnkI3+UgKbIg7ml2FoSMU8s3HP3V/FOhvp6V5P6y"
                     "t2okxABbw13WQPrzeUCZ9pRLgB3TnY59wsWM2SlynWEG/u/pFHyzuvkmtrGZtjZfITm7bfMnGy8FTOox4PfzCu4bysKl"
                     "Ubhc/yJ0fzI/+XsT2gKasXETzlmx6vd4qKgKWP5U9OJVh+Cx//npFDCBI2Tba8JK+Cg==",
        "SigningCertURL":
            "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-7ff5318490ec183fbaddaa2a969abfda.pem",
        "UnsubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:"
                          "us-east-1:364852123998:test-email:0fe0bffc-6470-4502-9414-d5e3d9fdd71e",
    }

    valid_msg_missing_fields = {
        "Type": "Notification",
        "MessageId": "71a6b82e-0f1a-58db-b902-e2ef60f87541",
        "TopicArn": "arn:aws:sns:us-east-1:364852123998:test-email",
        # Normally you'd see a subject key/value pair here, but not on this
        # notification.
        "Message": '{"notificationType":"Bounce","bounce":{"feedbackId":"0100017fe7044080-b95aeb18-3fb8-408a-be9b-'
                   '15fdbac3945a-000000","bounceType":"Permanent","bounceSubType":"General","bouncedRecipients":['
                   '{"emailAddress":"bounce@simulator.amazonses.com","action":"failed","status":"5.1.1",'
                   '"diagnosticCode":"smtp; 550 5.1.1 user unknown"}],"timestamp":"2022-04-01T21:24:49.000Z",'
                   '"remoteMtaIp":"3.231.136.178","reportingMTA":"dns; a48-30.smtp-out.amazonses.com"},"mail":'
                   '{"timestamp":"2022-04-01T21:24:49.422Z","source":"jesus.islasf@alumno.buap.mx","sourceArn":'
                   '"arn:aws:ses:us-east-1:364852123998:identity/jesus.islasf@alumno.buap.mx","sourceIp":'
                   '"189.203.131.80","sendingAccountId":"364852123998","messageId":'
                   '"0100017fe7043e8e-fc9c357d-a9a4-49bc-a4b4-fa984009d568-000000","destination":'
                   '["bounce@simulator.amazonses.com"],"headersTruncated":false,"headers":[{"name":'
                   '"From","value":"jesus.islasf@alumno.buap.mx"},{"name":"To","value":'
                   '"bounce@simulator.amazonses.com"},{"name":"Subject","value":"Subject Test"},'
                   '{"name":"MIME-Version","value":"1.0"},{"name":"Content-Type","value":'
                   '"multipart/alternative;  boundary=\\"----=_Part_2196631_1474166380.1648848289426\\""}],'
                   '"commonHeaders":{"from":["jesus.islasf@alumno.buap.mx"],"to":["bounce@simulator.amazonses.com"],'
                   '"subject":"Subject Test"}}}',
        "Timestamp": "2022-04-01T21:24:50.200Z",
        "SignatureVersion": "1",
        "Signature": "K27nwTcT0qTPKEQP3noOWV21gDGB6XnLXSwN2i+4176naErwyDSd72w44UesYE/KaRXU+Kusi7b8uoLYPOcYXHH45UCFMrSt"
                     "f9nzu0uIZdMSd7cFGPm0KAxqoDcP9UQw0+ssK1rjVWkywTYmeDyFF/j3IQZxTA/vINOLYbrmMKhyJUPjcZZwdgLmlKcNfKJ5"
                     "PKmg5WXlr8nWtjW3K+k725nkoAZemuAFt3PmA2k35JoHphkcOBjV2f1qR9zJTOgrVQ1d6k2v6t8G7Nlg6FP5OiwThgKHkehI"
                     "PfJfLhTmo05tfPCBzXYMzDbnX+HLidvkyibHlalRl/DuDxXXL7SUiA==",
        "SigningCertURL": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-"
                          "7ff5318490ec183fbaddaa2a969abfda.pem",
        "UnsubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn="
                          "arn:aws:sns:us-east-1:364852123998:test-email:0fe0bffc-6470-4502-9414-d5e3d9fdd71e",
    }

    def tearDown(self):
        # Reset the cache after each test
        clear_cert_cache()

    @skipIf(requests is None, "requests is not installed")
    @skipIf(x509 is None, "cryptography is not installed")
    def test_load_certificate(self):
        verifier = BounceMessageVerifier({})
        with mock.patch.object(verifier, "_get_cert_url") as get_cert_url:
            get_cert_url.return_value = "http://www.example.com/"
            with mock.patch.object(requests, "get") as request_get:
                request_get.return_value.status_code = 200
                request_get.return_value.content = "Spam"
                with mock.patch.object(
                    x509, "load_pem_x509_certificate"
                ) as load_cert_string:
                    self.assertEqual(
                        verifier.certificate, load_cert_string.return_value
                    )

    @skipIf(requests is None, "requests is not installed")
    @skipIf(x509 is None, "cryptography is not installed")
    def test_valid_msg_validates(self):
        """Does a valid message get validated properly?"""
        verifier = BounceMessageVerifier(self.valid_msg)
        with mock.patch.object(requests, "get") as request_get:
            request_get.return_value.content = self.VALID_CERT
            request_get.return_value.status_code = 200
            self.assertTrue(verifier.is_verified())

    @skipIf(requests is None, "requests is not installed")
    @skipIf(x509 is None, "cryptography is not installed")
    def test_valid_msg_missing_fields_validates(self):
        """Does a valid message with missing fields get validated properly?"""
        verifier = BounceMessageVerifier(self.valid_msg_missing_fields)
        with mock.patch.object(requests, "get") as request_get:
            request_get.return_value.content = self.VALID_CERT
            request_get.return_value.status_code = 200
            self.assertTrue(verifier.is_verified())

    @skipIf(requests is None, "requests is not installed")
    @skipIf(x509 is None, "cryptography is not installed")
    def test_invalid_message_fails(self):
        """Does an invalid message fail validation?"""
        verifier = BounceMessageVerifier(self.simple_msg)
        self.assertFalse(verifier.is_verified())

    @skipIf(requests is None, "requests is not installed")
    @skipIf(x509 is None, "cryptography is not installed")
    def test_cert_is_cached(self):
        """Does the certificate get cached properly?"""
        verifier = BounceMessageVerifier(self.valid_msg)
        with mock.patch.object(requests, "get") as request_get, mock.patch.object(
            x509, "load_pem_x509_certificate"
        ):
            request_get.return_value.content = b"Spam"
            request_get.return_value.status_code = 200
            verifier.certificate
            verifier.certificate
            request_get.assert_called_once()

    def test_get_cert_url(self):
        """
        Test url trust verification
        """
        cert_url = (
            "https://sns.test-example.amazonaws.com/SimpleNotificationService-abcd.pem"
        )
        verifier = BounceMessageVerifier(
            {
                "SigningCertURL": cert_url,
            }
        )
        self.assertEqual(verifier._get_cert_url(), cert_url)

    def test_http_cert_url(self):
        """
        Test url trust verification. Non-https urls should be rejected.
        """
        verifier = BounceMessageVerifier(
            {
                "SigningCertURL": "http://amazonaws.com/",
            }
        )
        self.assertEqual(verifier._get_cert_url(), None)

    def test_untrusted_cert_url_domain(self):
        """
        Test url trust verification. Untrusted domains should be rejected.
        """
        verifier = BounceMessageVerifier(
            {
                "SigningCertURL": "https://www.example.com/",
            }
        )
        self.assertEqual(verifier._get_cert_url(), None)

    def test_get_bytes_to_sign(self):
        verifier = BounceMessageVerifier(self.simple_msg)
        actual_result = verifier._get_bytes_to_sign()
        correct_result = (
            b"Message\nMessage text\n"
            b"MessageId\nSome ID\n"
            b"Subject\nEquity for all\n"
            b"Timestamp\nYesterday\n"
            b"TopicArn\narn:aws...\n"
            b"Type\nNotification\n"
        )
        self.assertEqual(actual_result, correct_result)
        self.assertTrue(isinstance(actual_result, bytes))
