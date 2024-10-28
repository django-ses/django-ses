import json
import os


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

def get_mock_received_email():
    return {
        'timestamp': '2024-10-27T17:13:33.684Z',
        'source': 'alexandernst@gmail.com',
        'messageId': '0bj0fp4ev5vrddnpflq7a17rpgmo7gnhslacdu01',
        'destination': ['foo@bar.com'],
        'headersTruncated': False,
        'headers': [
            {
                'name': 'Return-Path',
                'value': '<alexandernst@gmail.com>'
            },
            {
                'name': 'Received',
                'value': 'from mail-lf1-f45.google.com '
                         '(mail-lf1-f45.google.com [209.85.167.45]) by '
                         'inbound-smtp.us-east-1.amazonaws.com with '
                         'SMTP id '
                         '0bj0fp4ev5vrddnpflq7a17rpgmo7gnhslacdu01 for '
                         'foo@bar.com; Sun, 27 Oct 2024 '
                         '17:13:33 +0000 (UTC)'
            },
            {
                'name': 'X-SES-Spam-Verdict',
                'value': 'PASS'
            },
            {
                'name': 'X-SES-Virus-Verdict',
                'value': 'PASS'
            },
            {
                'name': 'Received-SPF',
                'value': 'pass (spfCheck: domain of _spf.google.com '
                         'designates 209.85.167.45 as permitted sender) '
                         'client-ip=209.85.167.45; '
                         'envelope-from=alexandernst@gmail.com; '
                         'helo=mail-lf1-f45.google.com;'
            },
            {
                'name': 'Authentication-Results',
                'value': 'amazonses.com; spf=pass (spfCheck: domain of '
                         '_spf.google.com designates 209.85.167.45 as '
                         'permitted sender) client-ip=209.85.167.45; '
                         'envelope-from=alexandernst@gmail.com; '
                         'helo=mail-lf1-f45.google.com; dkim=pass '
                         'header.i=@gmail.com; dmarc=pass '
                         'header.from=gmail.com;'
            },
            {
                'name': 'X-SES-RECEIPT',
                'value': 'AEFBQUFBQUFBQUFGOEpra2RyZWJPUlZ4d3NkTmhyZ2NBM0tlRktEeUNvVmt0NGdiMzNWUk1zWXlUZ2JwVktJU3NDdGZ4c'
                         'kRTMURZc0k3MlBaTlkyamRiY3daRFlxbEtCakFLeGppSGJrQkh0ejJ0N0xBcXJ2TDJlUTRJRHU4anJTRU1wMmpQVTFJZE'
                         'NVWHFiT2NpaVdkSWsxK1FMQTM0MXE2WXkrWW5CN3RHRkJkTDI3eUMvVnRrOWh5MVZRMlBiK2REWWFhY0xYYmVkL3VHYUd'
                         'oYWEvUmVFTytCMHpXUWR1eTJPUjFhQ3BBSHlBL2dieTBwSCt0QTFFRTh2SDVZcVJ1UjY4UDhac0tPZ01UTlRWZ2t2V0py'
                         'VFJCNlB6ZE9XZk10Y1lieFptbFdQV3Jjbk9pdWhqMlE9PQ=='
            },
            {
                'name': 'X-SES-DKIM-SIGNATURE',
                'value': 'a=rsa-sha256; q=dns/txt; '
                         'b=Y7IWMTNTKesfKhopRg2sjUOlVs5NeQKjSGavxaywj3KlWg+6ovOueCYZZK8/4QOmb6X2/sS29JYhrmyUvVXueoV1/iw'
                         'TPlxTDaKdMjsTILCMI+nEvVeV1e+r4t9BgV5EpT/kue2rDCd5eIJNFVB77qOAgM5UDcpt+C+APHuEjb4=; '
                         'c=relaxed/simple; '
                         's=ug7nbtf4gccmlpwj322ax3p6ow6yfsug; '
                         'd=amazonses.com; t=1730049214; v=1; '
                         'bh=3+TxY9fvf0zPnsSER7J7drTP5kKXNEg+Ue1NKN3mII4=; '
                         'h=From:To:Cc:Bcc:Subject:Date:Message-ID:MIME-Version:Content-Type:X-SES-RECEIPT;'
            },
            {
                'name': 'Received',
                'value': 'by mail-lf1-f45.google.com with SMTP id '
                         '2adb3069b0e04-539f84907caso3771922e87.3 for '
                         '<foo@bar.com>; Sun, 27 Oct 2024 '
                         '10:13:33 -0700 (PDT)'
            },
            {
                'name': 'DKIM-Signature',
                'value': 'v=1; a=rsa-sha256; c=relaxed/relaxed; '
                         'd=gmail.com; s=20230601; t=1730049212; '
                         'x=1730654012; darn=bar.com; '
                         'h=to:subject:message-id:date:from:mime-version:from:to:cc:subject:date:message-id:reply-to; '
                         'bh=3+TxY9fvf0zPnsSER7J7drTP5kKXNEg+Ue1NKN3mII4=; '
                         'b=FpIcePmBAbNZQErjJsePpOvUeNXuiimPXy+udQg47WrX3V8YtiKecCOuIjCoxk7AQ9yJYWOkZO4h2cjLGw4eyyMiHUl'
                         'qJC7zO7Uph7SDhPvPptxKXyv3L0Y4sMs/KWg3cHVDqOFX3zfFclsVpocfltJFj2nDDr5gQeXONsAn0nGPRK7b+cTlI2w/'
                         'RJy/q+MNThsjrB4JQurHbGhTcHb+B3cZtkHfClX+PzGZ+DkSsx8pdDZ/SsovGJIKXOgeaagJfO9pdt2muzJBBHBCw0sJ8'
                         '4FGmMbOYWY0OuTTZRugq2OMe51UlAqZOim2bVVWwPAmrD4bQ5rsFK9ufctPsblVDA=='
            },
            {
                'name': 'X-Google-DKIM-Signature',
                'value': 'v=1; a=rsa-sha256; c=relaxed/relaxed; '
                         'd=1e100.net; s=20230601; t=1730049212; '
                         'x=1730654012; '
                         'h=to:subject:message-id:date:from:mime-version:x-gm-message-state '
                         ':from:to:cc:subject:date:message-id:reply-to; '
                         'bh=3+TxY9fvf0zPnsSER7J7drTP5kKXNEg+Ue1NKN3mII4=; '
                         'b=viYdJJci/NjMkwze8dOZmUn5Zerb6LFFUdu6oQUhaOAD2yvtPxjoh4ToKgcomJVjPA '
                         '8Gxk53YQyAvPsYIsTGCBbiU6PzXcfG4cvWqgJw6CdGRJ0POiSXxmMxcljaoISrzSu8Lz '
                         'HHMxQ57FVxq4sud5aBSqIM9Axt3M0nIrbHDc+eOcYHsVd1svc1n9Mbqnftvbj6veLi+W '
                         'yb+GSRJyf4m2zpyeM8d2cLxFj4+IDEtYTmYX6hd8qtqf5uZYoAKfMRMIASY7binH/DRo '
                         'cxsgMi/XVGRxIACi0BFIQqs/pP0E04grULFnfFRE5S1uBv6iMtcQ2H21seQuboyFKqbs '
                         'lIQw=='
            },
            {
                'name': 'X-Gm-Message-State',
                'value': 'AOJu0YyeijzszzCRTvcUvLjjNwVZiIjxnL4vC7NQoMNHxqeCXbMFfYQ6 '
                         'eWFopGZVYLIoc62feiIAC4lU730b5FqR1gUnNo+m0quipOQUTJ/VbnQ52b35fSlv2yysZpqrGPo '
                         '2nxQAeb7zHSKQJodJlcC5zpCH0DhvfQ=='
            },
            {
                'name': 'X-Google-Smtp-Source',
                'value': 'AGHT+IHMZZbLZB56p/cTh66TxY/jz9cltZNQvoRAcbzc5RjUQmYKo8nMnl1LLcUlZcx0HsntJ8vAf2CbXPfqoT5rpPU='
            },
            {
                'name': 'X-Received',
                'value': 'by 2002:a05:6512:238a:b0:539:f949:c027 with '
                         'SMTP id '
                         '2adb3069b0e04-53b348f9b74mr2135393e87.18.1730049211812; '
                         'Sun, 27 Oct 2024 10:13:31 -0700 (PDT)'
            },
            {
                'name': 'MIME-Version',
                'value': '1.0'
            },
            {
                'name': 'From',
                'value': '"Alexander Nestorov (alexandernst)" <alexandernst@gmail.com>'
            },
            {
                'name': 'Date',
                'value': 'Sun, 27 Oct 2024 18:12:55 +0100'
            },
            {
                'name': 'Message-ID',
                'value': '<CACuz9s0EbFBFEdgJN6Pfc74mQ6+-S36UEZXO1=pbabnGx5ObOw@mail.gmail.com>'
            },
            {
                'name': 'Subject',
                'value': 'test'
            },
            {
                'name': 'To',
                'value': 'foo@bar.com'
            },
            {
                'name': 'Content-Type',
                'value': 'multipart/alternative; boundary="000000000000b6d36a0625787884"'
            }
        ],
        'commonHeaders': {
            'returnPath': 'alexandernst@gmail.com',
            'from': [
                '"Alexander Nestorov (alexandernst)" <alexandernst@gmail.com>'
            ],
            'date': 'Sun, 27 Oct 2024 18:12:55 +0100',
            'to': [
                'foo@bar.com'
            ],
            'messageId': '<CACuz9s0EbFBFEdgJN6Pfc74mQ6+-S36UEZXO1=pbabnGx5ObOw@mail.gmail.com>',
            'subject': 'test'
        }
    }


def get_mock_receipt_s3():
    return {
        "timestamp": "2012-05-25T14:59:38.605-07:00",
        "processingTimeMillis": 825,
        "recipients": ["foo@bar.com"],
        "spamVerdict": {"status": "PASS"},
        "virusVerdict": {"status": "PASS"},
        "spfVerdict": {"status": "PASS"},
        "dkimVerdict": {"status": "PASS"},
        "dmarcVerdict": {"status": "PASS"},
        "action": {
            "type": "S3",
            "topicArn": "arn:aws:sns:us-east-1:112310073099:inbox-foo-bar",
            "bucketName": "django-ses-test-inbox",
            "objectKey": "0bj0fp4ev5vrddnpflq7a17rpgmo7gnhslacdu01"
        }
    }


def get_mock_receipt_sns():
    return {
        "timestamp": "2012-05-25T14:59:38.605-07:00",
        "processingTimeMillis": 825,
        "recipients": ["foo@bar.com"],
        "spamVerdict": {"status": "PASS"},
        "virusVerdict": {"status": "PASS"},
        "spfVerdict": {"status": "PASS"},
        "dkimVerdict": {"status": "PASS"},
        "dmarcVerdict": {"status": "PASS"},
        "action": {
            "type": "SNS",
            "topicArn": "arn:aws:sns:us-east-1:112310073099:inbox-foo-bar",
            "encoding": "BASE64",
        }
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


def get_mock_received_s3():
    mail = get_mock_received_email()
    receipt = get_mock_receipt_s3()

    message = {
        "notificationType": "Received",
        "mail": mail,
        "receipt": receipt,
    }
    notification = get_mock_notification(message)
    return mail, None, receipt, notification


def get_mock_received_sns():
    mail = get_mock_received_email()
    receipt = get_mock_receipt_sns()

    fpath = os.path.join(os.path.dirname(__file__), "email_content.base64")
    content = open(fpath, "r").read()

    message = {
        "notificationType": "Received",
        "mail": mail,
        "receipt": receipt,
        "content": content,
    }
    notification = get_mock_notification(message)
    return mail, content, receipt, notification
