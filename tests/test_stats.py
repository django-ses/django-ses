import pytz
from datetime import datetime

from django.test import TestCase

from django_ses.views import emails_parse, stats_to_list, sum_stats

# Mock of what boto's SESConnection.get_send_statistics() returns
STATS_DICT = {
    u'SendDataPoints': [
        {
            u'Bounces': 1,
            u'Complaints': 0,
            u'DeliveryAttempts': 11,
            u'Rejects': 0,
            u'Timestamp':
                datetime(2011, 2, 28, 13, 50, tzinfo=pytz.utc),
        },
        {
            u'Bounces': 1,
            u'Complaints': 0,
            u'DeliveryAttempts': 3,
            u'Rejects': 0,
            u'Timestamp':
                datetime(2011, 2, 24, 23, 35, tzinfo=pytz.utc),
        },
        {
            u'Bounces': 0,
            u'Complaints': 2,
            u'DeliveryAttempts': 8,
            u'Rejects': 0,
            u'Timestamp':
                datetime(2011, 2, 24, 16, 35, tzinfo=pytz.utc),
        },
        {
            u'Bounces': 0,
            u'Complaints': 2,
            u'DeliveryAttempts': 33,
            u'Rejects': 0,
            u'Timestamp':
                datetime(2011, 2, 25, 20, 35, tzinfo=pytz.utc),
        },
        {
            u'Bounces': 0,
            u'Complaints': 0,
            u'DeliveryAttempts': 3,
            u'Rejects': 3,
            u'Timestamp':
                datetime(2011, 2, 28, 23, 35, tzinfo=pytz.utc),
        },
        {
            u'Bounces': 0,
            u'Complaints': 0,
            u'DeliveryAttempts': 2,
            u'Rejects': 3,
            u'Timestamp':
                datetime(2011, 2, 25, 22, 50, tzinfo=pytz.utc),
        },
        {
            u'Bounces': 0,
            u'Complaints': 0,
            u'DeliveryAttempts': 6,
            u'Rejects': 0,
            u'Timestamp':
                datetime(2011, 3, 1, 13, 20, tzinfo=pytz.utc),
        },
    ],
}

VERIFIED_EMAIL_DICT = {
    u'VerifiedEmailAddresses': [
        u'test2@example.com',
        u'test1@example.com',
        u'test3@example.com'
    ],
    u'ResponseMetadata': {
        u'RequestId': u'9afe9c18-44ed-11e0-802a-25a1a14c5a6e',
        u'HTTPStatusCode': 200,
        u'HTTPHeaders': {
            u'x-amzn-requestid': u'9afe9c18-44ed-11e0-802a-25a1a14c5a6e',
            u'content-type': u'text/xml',
            u'content-length': u'536',
            u'date': u'Thu, 20 Aug 2020 05:06:35 GMT'
        },
        u'RetryAttempts': 0
    }
}


class StatParsingTest(TestCase):
    def setUp(self):
        self.stats_dict = STATS_DICT
        self.emails_dict = VERIFIED_EMAIL_DICT

    def test_stat_to_list(self):
        expected_list = [
            {
                u'Bounces': 0,
                u'Complaints': 2,
                u'DeliveryAttempts': 8,
                u'Rejects': 0,
                u'Timestamp':
                    datetime(2011, 2, 24, 16, 35, tzinfo=pytz.utc),
            },
            {
                u'Bounces': 1,
                u'Complaints': 0,
                u'DeliveryAttempts': 3,
                u'Rejects': 0,
                u'Timestamp':
                    datetime(2011, 2, 24, 23, 35, tzinfo=pytz.utc),
            },
            {
                u'Bounces': 0,
                u'Complaints': 2,
                u'DeliveryAttempts': 33,
                u'Rejects': 0,
                u'Timestamp':
                    datetime(2011, 2, 25, 20, 35, tzinfo=pytz.utc),
            },
            {
                u'Bounces': 0,
                u'Complaints': 0,
                u'DeliveryAttempts': 2,
                u'Rejects': 3,
                u'Timestamp':
                    datetime(2011, 2, 25, 22, 50, tzinfo=pytz.utc),
            },
            {
                u'Bounces': 1,
                u'Complaints': 0,
                u'DeliveryAttempts': 11,
                u'Rejects': 0,
                u'Timestamp':
                    datetime(2011, 2, 28, 13, 50, tzinfo=pytz.utc),
            },
            {
                u'Bounces': 0,
                u'Complaints': 0,
                u'DeliveryAttempts': 3,
                u'Rejects': 3,
                u'Timestamp':
                    datetime(2011, 2, 28, 23, 35, tzinfo=pytz.utc),
            },
            {
                u'Bounces': 0,
                u'Complaints': 0,
                u'DeliveryAttempts': 6,
                u'Rejects': 0,
                u'Timestamp':
                    datetime(2011, 3, 1, 13, 20, tzinfo=pytz.utc),
            },
        ]
        actual = stats_to_list(self.stats_dict, localize=False)

        self.assertEqual(len(actual), len(expected_list))
        self.assertEqual(actual, expected_list)

    def test_emails_parse(self):
        expected_list = [
            u'test1@example.com',
            u'test2@example.com',
            u'test3@example.com',
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
