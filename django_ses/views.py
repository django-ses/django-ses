import json
import warnings

import boto3
import pytz
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from django_ses.deprecation import RemovedInDjangoSES20Warning

try:
    from urllib.request import urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import urlopen, URLError
import copy
import logging


from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

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
    # Make a copy, so we don't change the original stats_dict.
    result = copy.deepcopy(stats_dict)
    datapoints = []
    if localize:
        current_tz = localize.timezone(settings.TIME_ZONE)
    else:
        current_tz = None
    for dp in result['SendDataPoints']:
        if current_tz:
            utc_dt = dp['Timestamp']
            dp['Timestamp'] = current_tz.normalize(
                utc_dt.astimezone(current_tz))
        datapoints.append(dp)

    datapoints.sort(key=lambda x: x['Timestamp'])

    return datapoints


def emails_parse(emails_dict):
    """
    Parse the output of ``SESConnection.list_verified_emails()`` and get
    a list of emails.
    """
    return sorted([email for email in emails_dict['VerifiedEmailAddresses']])


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
        t_bounces += dp['Bounces']
        t_complaints += dp['Complaints']
        t_delivery_attempts += dp['DeliveryAttempts']
        t_rejects += dp['Rejects']

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

    ses_conn = boto3.client(
        'ses',
        aws_access_key_id=settings.ACCESS_KEY,
        aws_secret_access_key=settings.SECRET_KEY,
        region_name=settings.AWS_SES_REGION_NAME,
        endpoint_url=settings.AWS_SES_REGION_ENDPOINT_URL,
    )

    quota_dict = ses_conn.get_send_quota()
    verified_emails_dict = ses_conn.list_verified_email_addresses()
    stats = ses_conn.get_send_statistics()

    verified_emails = emails_parse(verified_emails_dict)
    ordered_data = stats_to_list(stats)
    summary = sum_stats(ordered_data)

    extra_context = {
        'title': 'SES Statistics',
        'datapoints': ordered_data,
        '24hour_quota': quota_dict['Max24HourSend'],
        '24hour_sent': quota_dict['SentLast24Hours'],
        '24hour_remaining':
            quota_dict['Max24HourSend'] -
            quota_dict['SentLast24Hours'],
        'persecond_rate': quota_dict['MaxSendRate'],
        'verified_emails': verified_emails,
        'summary': summary,
        'access_key': settings.ACCESS_KEY,
        'local_time': True,
    }

    response = render(request, 'django_ses/send_stats.html', extra_context)

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

    SNS message signatures are verified by default. This functionality can
    be disabled by setting AWS_SES_VERIFY_EVENT_SIGNATURES to False.
    However, this is not recommended.
    See: http://docs.amazonwebservices.com/sns/latest/gsg/SendMessageToHttp.verify.signature.html
    """
    warnings.warn(
        'views.handle_bounce is deprecated. You can use SESEventWebhookView instead. '
        'It handles send, open, click events in addition to '
        'bounce, complaint, delivery and subscription confirmation events.',
        RemovedInDjangoSES20Warning,
    )

    raw_json = request.body

    try:
        notification = json.loads(raw_json.decode('utf-8'))
    except ValueError as e:
        # TODO: What kind of response should be returned here?
        logger.warning(u'Received bounce with bad JSON: "%s"', e)
        return HttpResponseBadRequest()

    # Verify the authenticity of the bounce message.
    if (settings.VERIFY_BOUNCE_SIGNATURES and
            not utils.verify_bounce_message(notification)):
        # Don't send any info back when the notification is not
        # verified. Simply, don't process it.
        logger.info(
            u'Received unverified notification: Type: %s',
            notification.get('Type'),
            extra={
                'notification': notification,
            },
        )
        return HttpResponse()

    if notification.get('Type') in ('SubscriptionConfirmation',
                                    'UnsubscribeConfirmation'):
        # Process the (un)subscription confirmation.

        logger.info(
            u'Received subscription confirmation: TopicArn: %s',
            notification.get('TopicArn'),
            extra={
                'notification': notification,
            },
        )

        # Get the subscribe url and hit the url to confirm the subscription.
        subscribe_url = notification.get('SubscribeURL')
        try:
            urlopen(subscribe_url).read()
        except URLError as e:
            # Some kind of error occurred when confirming the request.
            logger.error(
                u'Could not confirm subscription: "%s"', e,
                extra={
                    'notification': notification,
                },
                exc_info=True,
            )
    elif notification.get('Type') == 'Notification':
        try:
            message = json.loads(notification['Message'])
        except ValueError as e:
            # The message isn't JSON.
            # Just ignore the notification.
            logger.warning(u'Received bounce with bad JSON: "%s"', e, extra={
                'notification': notification,
            })
        else:
            mail_obj = message.get('mail')
            event_type = message.get('eventType')

            if event_type == 'Bounce':
                # Bounce
                bounce_obj = message.get('bounce', {})

                # Logging
                feedback_id = bounce_obj.get('feedbackId')
                bounce_type = bounce_obj.get('bounceType')
                bounce_subtype = bounce_obj.get('bounceSubType')
                logger.info(
                    u'Received bounce notification: feedbackId: %s, bounceType: %s, bounceSubType: %s',
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
            elif event_type == 'Complaint':
                # Complaint
                complaint_obj = message.get('complaint', {})

                # Logging
                feedback_id = complaint_obj.get('feedbackId')
                feedback_type = complaint_obj.get('complaintFeedbackType')
                logger.info(
                    u'Received complaint notification: feedbackId: %s, feedbackType: %s',
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
            elif event_type == 'Delivery':
                # Delivery
                delivery_obj = message.get('delivery', {})

                # Logging
                feedback_id = delivery_obj.get('feedbackId')
                feedback_type = delivery_obj.get('deliveryFeedbackType')
                logger.info(
                    u'Received delivery notification: feedbackId: %s, feedbackType: %s',
                    feedback_id, feedback_type,
                    extra={
                        'notification': notification,
                    },
                )

                signals.delivery_received.send(
                    sender=handle_bounce,
                    mail_obj=mail_obj,
                    delivery_obj=delivery_obj,
                    raw_message=raw_json,
                )
            else:
                # We received an unknown notification type. Just log and
                # ignore it.
                logger.warning(u"Received unknown event", extra={
                    'notification': notification,
                })
    else:
        logger.info(
            u'Received unknown notification type: %s',
            notification.get('Type'),
            extra={
                'notification': notification,
            },
        )

    # AWS will consider anything other than 200 to be an error response and
    # resend the SNS request. We don't need that so we return 200 here.
    return HttpResponse()


@method_decorator(csrf_exempt, name='dispatch')
class SESEventWebhookView(View):
    """
    Handle a email sending event via an SNS webhook.

    Parse the event message and send the appropriate signal.
    <eventType> -> <signal>
    bounce -> bounce_received
    complaint -> complaint_received
    delivery -> delivery_received
    send -> send_received
    open -> open_received
    click -> click_received
    See: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/monitor-sending-activity.html
    See: http://docs.aws.amazon.com/sns/latest/gsg/json-formats.html#http-subscription-confirmation-json
    See: http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/NotificationsViaSNS.html

    In addition to email bounce requests this endpoint also supports the SNS
    subscription confirmation request. This request is sent to the SNS
    subscription endpoint when the subscription is registered.
    See: http://docs.aws.amazon.com/sns/latest/gsg/Subscribe.html

    For the format of the SNS subscription confirmation request see this URL:
    http://docs.aws.amazon.com/sns/latest/gsg/json-formats.html#http-subscription-confirmation-json

    SNS message signatures are verified by default. This functionality can
    be disabled by setting AWS_SES_VERIFY_EVENT_SIGNATURES to False.
    However, this is not recommended.
    See: http://docs.amazonwebservices.com/sns/latest/gsg/SendMessageToHttp.verify.signature.html
    """

    def post(self, request, *args, **kwargs):
        raw_json = request.body

        try:
            notification = json.loads(raw_json.decode('utf-8'))
        except ValueError as e:
            # TODO: What kind of response should be returned here?
            logger.warning(u'Received bounce with bad JSON: "%s"', e)
            return HttpResponseBadRequest()

        # Verify the authenticity of the event message.
        if settings.VERIFY_EVENT_SIGNATURES and not self.verify_event_message(notification):
            # Don't send any info back when the notification is not
            # verified. Simply, don't process it.
            logger.info(
                u'Received unverified notification: Type: %s',
                notification.get('Type'),
                extra={
                    'notification': notification,
                },
            )
            return HttpResponse()

        if notification.get('Type') in ('SubscriptionConfirmation', 'UnsubscribeConfirmation'):
            # Process the (un)subscription confirmation.
            self.confirm_sns_notification(notification)
        elif notification.get('Type') == 'Notification':
            try:
                message = json.loads(notification['Message'])
            except ValueError as e:
                # The message isn't JSON.
                # Just ignore the notification.
                logger.warning(u'Received bounce with bad JSON: "%s"', e, extra={
                    'notification': notification,
                })
            else:
                event_type = message.get('eventType')
                if event_type == 'Bounce':
                    self.handle_bounce(notification, message)
                elif event_type == 'Complaint':
                    self.handle_complaint(notification, message)
                elif event_type == 'Delivery':
                    self.handle_delivery(notification, message)
                elif event_type == 'Send':
                    self.handle_send(notification, message)
                elif event_type == 'Open':
                    self.handle_open(notification, message)
                elif event_type == 'Click':
                    self.handle_click(notification, message)
                else:
                    self.handle_unknown_event_type(notification, message)
        else:
            self.handle_unknown_notification_type(notification)

        # AWS will consider anything other than 200 to be an error response and
        # resend the SNS request. We don't need that so we return 200 here.
        return HttpResponse()

    def confirm_sns_notification(self, notification):
        utils.confirm_sns_subscription(notification)

    def verify_event_message(self, notification):
        return utils.verify_event_message(notification)

    def handle_unknown_notification_type(self, notification):
        logger.info(
            u'Received unknown notification type: %s',
            notification.get('Type'),
            extra={
                'notification': notification,
            },
        )

    def handle_bounce(self, notification, message):
        mail_obj = message.get('mail')
        bounce_obj = message.get('bounce', {})

        # Logging
        feedback_id = bounce_obj.get('feedbackId')
        bounce_type = bounce_obj.get('bounceType')
        bounce_subtype = bounce_obj.get('bounceSubType')
        logger.info(
            u'Received bounce notification: feedbackId: %s, bounceType: %s, bounceSubType: %s',
            feedback_id, bounce_type, bounce_subtype,
            extra={
                'notification': notification,
            },
        )

        signals.bounce_received.send(
            sender=self.handle_bounce,
            mail_obj=mail_obj,
            bounce_obj=bounce_obj,
            raw_message=self.request.body,
        )

    def handle_complaint(self, notification, message):
        mail_obj = message.get('mail')
        complaint_obj = message.get('complaint', {})

        # Logging
        feedback_id = complaint_obj.get('feedbackId')
        feedback_type = complaint_obj.get('complaintFeedbackType')
        logger.info(
            u'Received complaint notification: feedbackId: %s, feedbackType: %s',
            feedback_id, feedback_type,
            extra={
                'notification': notification,
            },
        )

        signals.complaint_received.send(
            sender=self.handle_complaint,
            mail_obj=mail_obj,
            complaint_obj=complaint_obj,
            raw_message=self.request.body,
        )

    def handle_delivery(self, notification, message):
        mail_obj = message.get('mail')
        delivery_obj = message.get('delivery', {})

        # Logging
        feedback_id = delivery_obj.get('feedbackId')
        feedback_type = delivery_obj.get('deliveryFeedbackType')
        logger.info(
            u'Received delivery notification: feedbackId: %s, feedbackType: %s',
            feedback_id, feedback_type,
            extra={
                'notification': notification,
            },
        )

        signals.delivery_received.send(
            sender=self.handle_delivery,
            mail_obj=mail_obj,
            delivery_obj=delivery_obj,
            raw_message=self.request.body,
        )

    def handle_send(self, notification, message):
        mail_obj = message.get('mail')
        send_obj = message.get('send', {})

        # Logging
        feedback_id = send_obj.get('feedbackId')
        feedback_type = send_obj.get('deliveryFeedbackType')
        logger.info(
            u'Received send notification: feedbackId: %s, feedbackType: %s',
            feedback_id, feedback_type,
            extra={
                'notification': notification,
            },
        )

        signals.send_received.send(
            sender=self.handle_send,
            mail_obj=mail_obj,
            send_obj=send_obj,
            raw_message=self.request.body,
        )

    def handle_open(self, notification, message):
        mail_obj = message.get('mail')
        open_obj = message.get('open', {})

        # Logging
        feedback_id = open_obj.get('feedbackId')
        feedback_type = open_obj.get('deliveryFeedbackType')
        logger.info(
            u'Received open notification: feedbackId: %s, feedbackType: %s',
            feedback_id, feedback_type,
            extra={
                'notification': notification,
            },
        )

        signals.open_received.send(
            sender=self.handle_open,
            mail_obj=mail_obj,
            open_obj=open_obj,
            raw_message=self.request.body,
        )

    def handle_click(self, notification, message):
        mail_obj = message.get('mail')
        click_obj = message.get('click', {})

        # Logging
        feedback_id = click_obj.get('feedbackId')
        feedback_type = click_obj.get('deliveryFeedbackType')
        logger.info(
            u'Received click notification: feedbackId: %s, feedbackType: %s',
            feedback_id, feedback_type,
            extra={
                'notification': notification,
            },
        )

        signals.click_received.send(
            sender=self.handle_click,
            mail_obj=mail_obj,
            click_obj=click_obj,
            raw_message=self.request.body,
        )

    def handle_unknown_event_type(self, notification, message):
        # We received an unknown notification type. Just log and
        # ignore it.
        logger.warning(u"Received unknown event", extra={
            'notification': notification,
        })
