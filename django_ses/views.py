import urllib2
import copy
import logging
from datetime import datetime

try:
    import pytz
except ImportError:
    pytz = None

from boto.regioninfo import RegionInfo
from boto.ses import SESConnection

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.template import RequestContext

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django_ses import settings
from django_ses import signals
from django_ses import utils

logger = logging.getLogger(__name__)

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

@require_POST
def handle_bounce(request):
    """
    Handle a bounced email via an SNS webhook.

    Parse the bounced message and send the appropriate signal.
    For bounce messages the bounce_received signal is called.
    For complaint messages the complaint_received signal is called.
    See: http://docs.aws.amazon.com/sns/latest/gsg/json-formats.html#http-subscription-confirmation-json
    See: http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/NotificationsViaSNS.html
    
    In addition to email bounce requests this endpoint also supports the SNS
    subscription confirmation request. This request is sent to the SNS
    subscription endpoint when the subscription is registered.
    See: http://docs.aws.amazon.com/sns/latest/gsg/Subscribe.html

    For the format of the SNS subscription confirmation request see this URL:
    http://docs.aws.amazon.com/sns/latest/gsg/json-formats.html#http-subscription-confirmation-json
    
    SNS message signatures are verified by default. This funcionality can
    be disabled by setting AWS_SES_VERIFY_BOUNCE_SIGNATURES to False.
    However, this is not recommended.
    See: http://docs.amazonwebservices.com/sns/latest/gsg/SendMessageToHttp.verify.signature.html
    """

    # For Django >= 1.4 use request.body, otherwise
    # use the old request.raw_post_data
    if hasattr(request, 'body'):
        raw_json = request.body
    else:
        raw_json = request.raw_post_data

    try:
        notification = json.loads(raw_json)
    except ValueError, e:
        # TODO: What kind of response should be returned here?
        logger.warning('Recieved bounce with bad JSON: "%s"', e)
        return HttpResponseBadRequest()

    # Verify the authenticity of the bounce message.
    if (settings.VERIFY_BOUNCE_SIGNATURES and 
            not utils.verify_bounce_message(notification)):
        # Don't send any info back when the notification is not
        # verified. Simply, don't process it.
        logger.info('Recieved unverified notification: Type: %s', 
            notification.get('Type'),
            extra={
                'notification': notification,
            },
        )
        return HttpResponse()

    if notification.get('Type') in ('SubscriptionConfirmation',
                                    'UnsubscribeConfirmation'):
        # Process the (un)subscription confirmation.

        logger.info('Recieved subscription confirmation: TopicArn: %s', 
            notification.get('TopicArn'),
            extra={
                'notification': notification,
            },
        )

        # Get the subscribe url and hit the url to confirm the subscription.
        subscribe_url = notification.get('SubscribeURL')
        try:
            urllib2.urlopen(subscribe_url).read()
        except urllib2.URLError, e:
            # Some kind of error occurred when confirming the request.
            logger.error('Could not confirm subscription: "%s"', e,
                extra={
                    'notification': notification,
                },
                exc_info=True,
            )
    elif notification.get('Type') == 'Notification':
        try:
            message = json.loads(notification['Message'])
        except ValueError, e:
            # The message isn't JSON.
            # Just ignore the notification.
            logger.warning('Recieved bounce with bad JSON: "%s"', e, extra={
                'notification': notification, 
            })
        else:
            mail_obj = message.get('mail')
            notification_type = message.get('notificationType')
            
            if notification_type == 'Bounce':
                # Bounce 
                bounce_obj = message.get('bounce', {})
                
                # Logging
                feedback_id = bounce_obj.get('feedbackId')
                bounce_type = bounce_obj.get('bounceType')
                bounce_subtype = bounce_obj.get('bounceSubType')
                logger.info(
                    'Recieved bounce notification: feedbackId: %s, bounceType: %s, bounceSubType: %s', 
                    feedback_id, bounce_type, bounce_subtype,
                    extra={
                        'notification': notification,
                    },
                )

                signals.bounce_received.send(
                    sender=handle_bounce,
                    mail_obj=mail_obj,
                    bounce_obj=bounce_obj,
                    raw_message=raw_json,
                )
            elif notification_type == 'Complaint':
                # Complaint
                complaint_obj = message.get('complaint', {})

                # Logging
                feedback_id = complaint_obj.get('feedbackId')
                feedback_type = complaint_obj.get('complaintFeedbackType')
                logger.info('Recieved complaint notification: feedbackId: %s, feedbackType: %s', 
                    feedback_id, feedback_type,
                    extra={
                        'notification': notification,
                    },
                )

                signals.complaint_received.send(
                    sender=handle_bounce,
                    mail_obj=mail_obj,
                    complaint_obj=complaint_obj,
                    raw_message=raw_json,
                )
            else:
                # We received an unknown notification type. Just log and
                # ignore it.
                logger.warning("Recieved unknown notification", extra={
                    'notification': notification,
                })
    else:
        logger.info('Recieved unknown notification type: %s', 
            notification.get('Type'),
            extra={
                'notification': notification,
            },
        )

    # AWS will consider anything other than 200 to be an error response and
    # resend the SNS request. We don't need that so we return 200 here.
    return HttpResponse()
