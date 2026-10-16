import datetime
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from django_ses.models import SESStat


class StatisticsRefreshTest(TestCase):
    def test_updates_each_counter_independently(self):
        initial = {"delivery_attempts": 5, "bounces": 0, "complaints": 0, "rejects": 0}
        api_fields = {
            "delivery_attempts": "DeliveryAttempts",
            "bounces": "Bounces",
            "complaints": "Complaints",
            "rejects": "Rejects",
        }
        date = datetime.date(2026, 10, 15)
        for field in initial:
            with self.subTest(field=field):
                SESStat.objects.update_or_create(date=date, defaults=initial)
                expected = dict(initial)
                expected[field] += 1
                point = {api_fields[key]: value for key, value in expected.items()}
                point["Timestamp"] = datetime.datetime(2026, 10, 15, tzinfo=datetime.timezone.utc)
                with patch("django_ses.management.commands.get_ses_statistics.boto3.client") as client:
                    client.return_value.get_send_statistics.return_value = {"SendDataPoints": [point]}
                    call_command("get_ses_statistics")
                stat = SESStat.objects.get(date=date)
                for key, value in expected.items():
                    self.assertEqual(getattr(stat, key), value)

    def test_unchanged_statistics_are_not_saved(self):
        date = datetime.date(2026, 10, 15)
        SESStat.objects.create(date=date, delivery_attempts=5, bounces=0, complaints=0, rejects=0)
        point = {
            "Timestamp": datetime.datetime(2026, 10, 15, tzinfo=datetime.timezone.utc),
            "DeliveryAttempts": 5,
            "Bounces": 0,
            "Complaints": 0,
            "Rejects": 0,
        }
        with patch("django_ses.management.commands.get_ses_statistics.boto3.client") as client:
            client.return_value.get_send_statistics.return_value = {"SendDataPoints": [point]}
            with patch.object(SESStat, "save") as save:
                call_command("get_ses_statistics")
            save.assert_not_called()
