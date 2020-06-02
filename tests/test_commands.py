import copy
import datetime
from unittest import mock

import boto3
from django.core.management import call_command
from django.test import TestCase

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


def fake_get_statistics():
    return {
        'SendDataPoints': data_points,
        'ResponseMetadata': {
            'RequestId': '1'
        }
    }


class SESCommandTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.connection = boto3.client(
            'ses',
            aws_access_key_id='ACCESS_KEY',
            aws_secret_access_key='SECRET_KEY',
        )

    def test_get_statistics(self):
        # Test the get_ses_statistics management command
        with mock.patch('boto3.client', return_value=self.connection):
            with mock.patch.object(self.connection, 'get_send_statistics', return_value=fake_get_statistics()):
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
        data_points_copy = copy.deepcopy(data_points)
        data_points_copy[0]['Complaints'] = '2'
        data_points_copy[0]['DeliveryAttempts'] = '3'
        data_points_copy[0]['Bounces'] = '4'
        data_points_copy[0]['Rejects'] = '5'

        def fake_get_statistics_copy():
            return {
                'SendDataPoints': data_points_copy,
                'ResponseMetadata': {
                    'RequestId': '1'
                }
            }

        with mock.patch('boto3.client', return_value=self.connection):
            with mock.patch.object(self.connection, 'get_send_statistics', return_value=fake_get_statistics_copy()):
                call_command('get_ses_statistics')
        stat = SESStat.objects.get(date='2012-01-01')
        self.assertEqual(stat.complaints, 2)
        self.assertEqual(stat.delivery_attempts, 3)
        self.assertEqual(stat.bounces, 4)
        self.assertEqual(stat.rejects, 5)
