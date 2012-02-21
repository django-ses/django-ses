import copy
from datetime import datetime

try:
    import pytz
except ImportError:
    pytz = None

from boto.regioninfo import RegionInfo
from boto.ses import SESConnection

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.template import RequestContext

from django_ses import settings

def superuser_only(view_func):
    """
    Limit a view to superuser only.
    """
    def _inner(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _inner


def stats_to_list(stats_dict, localize=pytz):
    """
    Parse the output of ``SESConnection.get_send_statistics()`` in to an
    ordered list of 15-minute summaries.
    """
    result = stats_dict['GetSendStatisticsResponse']['GetSendStatisticsResult']
    # Make a copy, so we don't change the original stats_dict.
    result = copy.deepcopy(result)
    datapoints = []
    if localize:
        current_tz = localize.timezone(settings.TIME_ZONE)
    else:
        current_tz = None
    for dp in result['SendDataPoints']:
        if current_tz:
            utc_dt = datetime.strptime(dp['Timestamp'], '%Y-%m-%dT%H:%M:%SZ')
            utc_dt = localize.utc.localize(utc_dt)
            dp['Timestamp'] = current_tz.normalize(
                utc_dt.astimezone(current_tz))
        datapoints.append(dp)

    datapoints.sort(key=lambda x: x['Timestamp'])

    return datapoints


def quota_parse(quota_dict):
    """
    Parse the output of ``SESConnection.get_send_quota()`` to just the results.
    """
    return quota_dict['GetSendQuotaResponse']['GetSendQuotaResult']


def emails_parse(emails_dict):
    """
    Parse the output of ``SESConnection.list_verified_emails()`` and get
    a list of emails.
    """
    result = emails_dict['ListVerifiedEmailAddressesResponse'][
        'ListVerifiedEmailAddressesResult']
    emails = [email for email in result['VerifiedEmailAddresses']]

    return sorted(emails)


def sum_stats(stats_data):
    """
    Summarize the bounces, complaints, delivery attempts and rejects from a
    list of datapoints.
    """
    t_bounces = 0
    t_complaints = 0
    t_delivery_attempts = 0
    t_rejects = 0
    for dp in stats_data:
        t_bounces += int(dp['Bounces'])
        t_complaints += int(dp['Complaints'])
        t_delivery_attempts += int(dp['DeliveryAttempts'])
        t_rejects += int(dp['Rejects'])

    return {
        'Bounces': t_bounces,
        'Complaints': t_complaints,
        'DeliveryAttempts': t_delivery_attempts,
        'Rejects': t_rejects,
    }


@superuser_only
def dashboard(request):
    """
    Graph SES send statistics over time.
    """
    cache_key = 'vhash:django_ses_stats'
    cached_view = cache.get(cache_key)
    if cached_view:
        return cached_view

    region = RegionInfo(
        name=settings.AWS_SES_REGION_NAME,
        endpoint=settings.AWS_SES_REGION_ENDPOINT)

    ses_conn = SESConnection(
        aws_access_key_id=settings.ACCESS_KEY,
        aws_secret_access_key=settings.SECRET_KEY,
        region=region)

    quota_dict = ses_conn.get_send_quota()
    verified_emails_dict = ses_conn.list_verified_email_addresses()
    stats = ses_conn.get_send_statistics()

    quota = quota_parse(quota_dict)
    verified_emails = emails_parse(verified_emails_dict)
    ordered_data = stats_to_list(stats)
    summary = sum_stats(ordered_data)

    extra_context = {
        'title': 'SES Statistics',
        'datapoints': ordered_data,
        '24hour_quota': quota['Max24HourSend'],
        '24hour_sent': quota['SentLast24Hours'],
        '24hour_remaining': float(quota['Max24HourSend']) -
                            float(quota['SentLast24Hours']),
        'persecond_rate': quota['MaxSendRate'],
        'verified_emails': verified_emails,
        'summary': summary,
        'access_key': ses_conn.gs_access_key_id,
        'local_time': True if pytz else False,
    }

    response = render_to_response(
        'django_ses/send_stats.html',
        extra_context,
        context_instance=RequestContext(request))

    cache.set(cache_key, response, 60 * 15)  # Cache for 15 minutes
    return response
