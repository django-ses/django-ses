from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from django.test import TestCase

from django_ses.views import emails_parse, stats_to_list, sum_stats

UTC = ZoneInfo('UTC')
CHICAGO = ZoneInfo('America/Chicago')

# Mock of what boto's SESConnection.get_send_statistics() returns
STATS_DICT = {
    'SendDataPoints': [
        {
            'Bounces': 1,
            'Complaints': 0,
            'DeliveryAttempts': 11,
            'Rejects': 0,
            'Timestamp':
                datetime(2011, 2, 28, 13, 50, tzinfo=UTC),
        },
        {
            'Bounces': 1,
            'Complaints': 0,
            'DeliveryAttempts': 3,
            'Rejects': 0,
            'Timestamp':
                datetime(2011, 2, 24, 23, 35, tzinfo=UTC),
        },
        {
            'Bounces': 0,
            'Complaints': 2,
            'DeliveryAttempts': 8,
            'Rejects': 0,
            'Timestamp':
                datetime(2011, 2, 24, 16, 35, tzinfo=UTC),
        },
        {
            'Bounces': 0,
            'Complaints': 2,
            'DeliveryAttempts': 33,
            'Rejects': 0,
            'Timestamp':
                datetime(2011, 2, 25, 20, 35, tzinfo=UTC),
        },
        {
            'Bounces': 0,
            'Complaints': 0,
            'DeliveryAttempts': 3,
            'Rejects': 3,
            'Timestamp':
                datetime(2011, 2, 28, 23, 35, tzinfo=UTC),
        },
        {
            'Bounces': 0,
            'Complaints': 0,
            'DeliveryAttempts': 2,
            'Rejects': 3,
            'Timestamp':
                datetime(2011, 2, 25, 22, 50, tzinfo=UTC),
        },
        {
            'Bounces': 0,
            'Complaints': 0,
            'DeliveryAttempts': 6,
            'Rejects': 0,
            'Timestamp':
                datetime(2011, 3, 1, 13, 20, tzinfo=UTC),
        },
    ],
}

VERIFIED_EMAIL_DICT = {
    'VerifiedEmailAddresses': [
        'test2@example.com',
        'test1@example.com',
        'test3@example.com'
    ],
    'ResponseMetadata': {
        'RequestId': '9afe9c18-44ed-11e0-802a-25a1a14c5a6e',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': '9afe9c18-44ed-11e0-802a-25a1a14c5a6e',
            'content-type': 'text/xml',
            'content-length': '536',
            'date': 'Thu, 20 Aug 2020 05:06:35 GMT'
        },
        'RetryAttempts': 0
    }
}


class StatParsingTest(TestCase):
    def setUp(self):
        self.stats_dict = STATS_DICT
        self.emails_dict = VERIFIED_EMAIL_DICT

    def test_stat_to_list(self):
        expected_list = [
            {
                'Bounces': 0,
                'Complaints': 2,
                'DeliveryAttempts': 8,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 24, 16, 35, tzinfo=UTC),
            },
            {
                'Bounces': 1,
                'Complaints': 0,
                'DeliveryAttempts': 3,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 24, 23, 35, tzinfo=UTC),
            },
            {
                'Bounces': 0,
                'Complaints': 2,
                'DeliveryAttempts': 33,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 25, 20, 35, tzinfo=UTC),
            },
            {
                'Bounces': 0,
                'Complaints': 0,
                'DeliveryAttempts': 2,
                'Rejects': 3,
                'Timestamp':
                    datetime(2011, 2, 25, 22, 50, tzinfo=UTC),
            },
            {
                'Bounces': 1,
                'Complaints': 0,
                'DeliveryAttempts': 11,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 28, 13, 50, tzinfo=UTC),
            },
            {
                'Bounces': 0,
                'Complaints': 0,
                'DeliveryAttempts': 3,
                'Rejects': 3,
                'Timestamp':
                    datetime(2011, 2, 28, 23, 35, tzinfo=UTC),
            },
            {
                'Bounces': 0,
                'Complaints': 0,
                'DeliveryAttempts': 6,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 3, 1, 13, 20, tzinfo=UTC),
            },
        ]
        actual = stats_to_list(self.stats_dict, localize=False)

        self.assertEqual(len(actual), len(expected_list))
        self.assertEqual(actual, expected_list)

    def test_stat_to_list_localize(self):
        expected_list = [
            {
                'Bounces': 0,
                'Complaints': 2,
                'DeliveryAttempts': 8,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 24, 10, 35, tzinfo=CHICAGO),
            },
            {
                'Bounces': 1,
                'Complaints': 0,
                'DeliveryAttempts': 3,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 24, 17, 35, tzinfo=CHICAGO),
            },
            {
                'Bounces': 0,
                'Complaints': 2,
                'DeliveryAttempts': 33,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 25, 14, 35, tzinfo=CHICAGO),
            },
            {
                'Bounces': 0,
                'Complaints': 0,
                'DeliveryAttempts': 2,
                'Rejects': 3,
                'Timestamp':
                    datetime(2011, 2, 25, 16, 50, tzinfo=CHICAGO),
            },
            {
                'Bounces': 1,
                'Complaints': 0,
                'DeliveryAttempts': 11,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 2, 28, 7, 50, tzinfo=CHICAGO),
            },
            {
                'Bounces': 0,
                'Complaints': 0,
                'DeliveryAttempts': 3,
                'Rejects': 3,
                'Timestamp':
                    datetime(2011, 2, 28, 17, 35, tzinfo=CHICAGO),
            },
            {
                'Bounces': 0,
                'Complaints': 0,
                'DeliveryAttempts': 6,
                'Rejects': 0,
                'Timestamp':
                    datetime(2011, 3, 1, 7, 20, tzinfo=CHICAGO),
            },
        ]
        actual = stats_to_list(self.stats_dict, localize=True)

        self.assertEqual(len(actual), len(expected_list))
        self.assertEqual(actual, expected_list)

    def test_emails_parse(self):
        expected_list = [
            'test1@example.com',
            'test2@example.com',
            'test3@example.com',
        ]
        actual = emails_parse(self.emails_dict)

        self.assertEqual(len(actual), len(expected_list))
        self.assertEqual(actual, expected_list)

    def test_sum_stats(self):
        expected = {
            'Bounces': 2,
            'Complaints': 4,
            'DeliveryAttempts': 66,
            'Rejects': 6,
        }

        stats = stats_to_list(self.stats_dict)
        actual = sum_stats(stats)

        self.assertEqual(actual, expected)
