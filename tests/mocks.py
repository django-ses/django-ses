import json


def get_mock_email():
    return {
        "timestamp": "2012-05-25T14:59:38.623-07:00",
        "messageId": "000001378603177f-7a5433e7-8edb-42ae-af10-f0181f34d6ee-000000",
        "source": "sender@example.com",
        "destination": [
            "recipient1@example.com",
            "recipient2@example.com",
            "recipient3@example.com",
            "recipient4@example.com"
        ]
    }


def get_mock_notification(message):
    return {
        "Type": "Notification",
        "MessageId": "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyTopic",
        "Subject": "Amazon SES Email Event Notification",
        "Message": json.dumps(message),
        "Timestamp": "2012-05-02T00:54:06.655Z",
        "SignatureVersion": "1",
        "Signature": "",
        "SigningCertURL": "",
        "UnsubscribeURL": ""
    }


def get_mock_bounce(type_specifier):
    mail = get_mock_email()
    bounce = {
        "bounceType": "Permanent",
        "bounceSubType": "General",
        "bouncedRecipients": [
            {
                "status": "5.0.0",
                "action": "failed",
                "diagnosticCode": "smtp; 550 user unknown",
                "emailAddress": "recipient1@example.com",
            },
            {
                "status": "4.0.0",
                "action": "delayed",
                "emailAddress": "recipient2@example.com",
            }
        ],
        "reportingMTA": "example.com",
        "timestamp": "2012-05-25T14:59:38.605-07:00",
        "feedbackId": "000001378603176d-5a4b5ad9-6f30-4198-a8c3-b1eb0c270a1d-000000",
    }

    message = {
        type_specifier: "Bounce",
        "mail": mail,
        "bounce": bounce,
    }
    notification = get_mock_notification(message)
    return mail, bounce, notification

def get_mock_complaint(type_specifier):
    mail = get_mock_email()
    complaint = {
        "userAgent": "ExampleCorp Feedback Loop (V0.01)",
        "complainedRecipients": [
            {
                "emailAddress": "recipient1@example.com"
            }
        ],
        "complaintFeedbackType": "abuse",
        "arrivalDate": "2009-12-03T04:24:21.000-05:00",
        "timestamp": "2012-05-25T14:59:38.623Z",
        "feedbackId": "000001378603177f-18c07c78-fa81-4a58-9dd1-fedc3cb8f49a-000000"
    }

    message = {
        type_specifier: "Complaint",
        "mail": mail,
        "complaint": complaint,
    }
    notification = get_mock_notification(message)
    return mail, complaint, notification


def get_mock_send():
    mail = get_mock_email()
    send = {}
    message = {
        "eventType": "Send",
        "mail": mail,
        "send": send,
    }
    notification = get_mock_notification(message)
    return mail, send, notification


def get_mock_delivery():
    mail = get_mock_email()
    delivery = {
        "timestamp": "2021-01-26T14:38:39.270Z",
        "processingTimeMillis": 1796,
        "recipients": ["recipient1@example.com"],
        "smtpResponse": "",
        "reportingMTA": ""
    }
    message = {
        "eventType": "Delivery",
        "mail": mail,
        "delivery": delivery,
    }
    notification = get_mock_notification(message)
    return mail, delivery, notification


def get_mock_open():
    mail = get_mock_email()
    open = {
        "timestamp": "2021-01-26T14:38:52.115Z",
        "userAgent": "Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0 (via ggpht.com GoogleImageProxy)",
        "ipAddress": "11.111.11.111"
    }
    message = {
        "eventType": "Open",
        "mail": mail,
        "open": open,
    }
    notification = get_mock_notification(message)
    return mail, open, notification


def get_mock_click():
    mail = get_mock_email()
    click = {
        "timestamp": "2021-01-26T14:38:55.540Z",
        "ipAddress": "11.111.11.111",
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                     "Version/14.0 Safari/605.1.15",
        "link": "github.com/django-ses/django-ses",
        "linkTags": None
    }
    message = {
        "eventType": "Click",
        "mail": mail,
        "click": click,
    }
    notification = get_mock_notification(message)
    return mail, click, notification
