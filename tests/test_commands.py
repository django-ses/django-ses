import datetime
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from django_ses.management.commands import get_ses_statistics as mod_get_ses_statistics
from django_ses.models import BlacklistedEmail, SESStat

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


class BlacklistCommandRTest(TestCase):
    def test_add_command(self):
        blacklisted = BlacklistedEmail.objects.all().count()
        self.assertEqual(blacklisted, 0)

        call_command('blacklist', '--add', 'foo@bar.com')

        blacklisted = BlacklistedEmail.objects.get(email='foo@bar.com')
        self.assertEqual(blacklisted.email, 'foo@bar.com')

    def test_delete_command(self):
        BlacklistedEmail.objects.create(email='foo@bar.com')
        BlacklistedEmail.objects.create(email='foo2@bar.com')
        BlacklistedEmail.objects.create(email='foo3@bar.com')

        blacklisted = BlacklistedEmail.objects.get(email='foo@bar.com')
        self.assertEqual(blacklisted.email, 'foo@bar.com')

        call_command('blacklist', '--delete', 'foo@bar.com')

        blacklisted = BlacklistedEmail.objects.filter(email='foo@bar.com').count()
        self.assertEqual(blacklisted, 0)

        blacklisted = BlacklistedEmail.objects.all().count()
        self.assertEqual(blacklisted, 2)

    def test_list_command(self):
        BlacklistedEmail.objects.create(email='foo@bar.com')
        BlacklistedEmail.objects.create(email='foo2@bar.com')
        BlacklistedEmail.objects.create(email='foo3@bar.com')

        out = StringIO()
        call_command('blacklist', '--list', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 3)
        self.assertIn('foo@bar.com', lines)
        self.assertIn('foo2@bar.com', lines)
        self.assertIn('foo3@bar.com', lines)

    def test_list_command_pagination(self):
        for i in range(55):
            BlacklistedEmail.objects.create(email=f'foo{i}@bar.com')

        out = StringIO()
        call_command('blacklist', '--list', '--page', '1', '--limit', '10', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 10)
        for i in range(10):
            self.assertIn(f'foo{i}@bar.com', lines)

        out = StringIO()
        call_command('blacklist', '--list', '--page', '2', '--limit', '10', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 10)
        for i in range(10, 20):
            self.assertIn(f'foo{i}@bar.com', lines)

        out = StringIO()
        call_command('blacklist', '--list', '--page', '6', '--limit', '10', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 5)
        for i in range(50, 55):
            self.assertIn(f'foo{i}@bar.com', lines)

        out = StringIO()
        call_command('blacklist', '--list', '--limit', '0', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 55)
        for i in range(55):
            self.assertIn(f'foo{i}@bar.com', lines)

    def test_search_command(self):
        BlacklistedEmail.objects.create(email='aaa@foo.com')
        BlacklistedEmail.objects.create(email='aaa@bar.com')
        BlacklistedEmail.objects.create(email='bbb@foo.com')
        BlacklistedEmail.objects.create(email='bbb@bar.com')
        BlacklistedEmail.objects.create(email='ccc@foo.com')
        BlacklistedEmail.objects.create(email='ccc@bar.com')

        out = StringIO()
        call_command('blacklist', '--search', 'bbb', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 2)
        self.assertIn('bbb@foo.com', lines)
        self.assertIn('bbb@bar.com', lines)

    def test_search_command_pagination(self):
        for i in range(55):
            BlacklistedEmail.objects.create(email=f'foo{i}@bar.com')

        out = StringIO()
        call_command('blacklist', '--search', 'foo', '--page', '1', '--limit', '10', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 10)
        for i in range(10):
            self.assertIn(f'foo{i}@bar.com', lines)

        out = StringIO()
        call_command('blacklist', '--search', 'foo', '--page', '2', '--limit', '10', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 10)
        for i in range(10, 20):
            self.assertIn(f'foo{i}@bar.com', lines)

        out = StringIO()
        call_command('blacklist', '--search', 'foo', '--page', '6', '--limit', '10', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 5)
        for i in range(50, 55):
            self.assertIn(f'foo{i}@bar.com', lines)

        out = StringIO()
        call_command('blacklist', '--search', 'foo', '--limit', '0', stdout=out)
        lines = out.getvalue().strip().splitlines()[1:]
        self.assertEqual(len(lines), 55)
        for i in range(55):
            self.assertIn(f'foo{i}@bar.com', lines)
