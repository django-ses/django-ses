import datetime

from django.core.management import call_command
from django.test import TestCase

from django_ses.management.commands import get_ses_statistics as mod_get_ses_statistics
from django_ses.models import SESStat

data_points = [
    {
        'Complaints': '1',
        'Timestamp': datetime.datetime(year=2012, month=1, day=1, hour=2),
        'DeliveryAttempts': '2',
        'Bounces': '3',
        'Rejects': '4'
    },
    {
        'Complaints': '1',
        'Timestamp': datetime.datetime(year=2012, month=1, day=3, hour=2),
        'DeliveryAttempts': '2',
        'Bounces': '3',
        'Rejects': '4'
    },
    {
        'Complaints': '1',
        'Timestamp': datetime.datetime(year=2012, month=1, day=3, hour=3),
        'DeliveryAttempts': '2',
        'Bounces': '3',
        'Rejects': '4'
    }
]


class FakeSESConnection:
    def __init__(self, *args, **kwargs):
        pass

    def get_send_statistics(self):
        return {
            'SendDataPoints': data_points,
            'ResponseMetadata': {
                'RequestId': '1'
            },
        }


class SESCommandTest(TestCase):

    def setUp(self):
        mod_get_ses_statistics.boto3.client = FakeSESConnection

    def test_get_statistics(self):
        # Test the get_ses_statistics management command
        call_command('get_ses_statistics')

        # Test that days with a single data point is saved properly
        stat = SESStat.objects.get(date='2012-01-01')
        self.assertEqual(stat.complaints, 1)
        self.assertEqual(stat.delivery_attempts, 2)
        self.assertEqual(stat.bounces, 3)
        self.assertEqual(stat.rejects, 4)

        # Test that days with multiple data points get saved properly
        stat = SESStat.objects.get(date='2012-01-03')
        self.assertEqual(stat.complaints, 2)
        self.assertEqual(stat.delivery_attempts, 4)
        self.assertEqual(stat.bounces, 6)
        self.assertEqual(stat.rejects, 8)

        # Changing data points should update database records too
        data_points[0]['Complaints'] = '2'
        data_points[0]['DeliveryAttempts'] = '3'
        data_points[0]['Bounces'] = '4'
        data_points[0]['Rejects'] = '5'

        call_command('get_ses_statistics')
        stat = SESStat.objects.get(date='2012-01-01')
        self.assertEqual(stat.complaints, 2)
        self.assertEqual(stat.delivery_attempts, 3)
        self.assertEqual(stat.bounces, 4)
        self.assertEqual(stat.rejects, 5)
