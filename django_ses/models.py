from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = (
    'SESStat',
    'SESNotificationBase',
    'BouncedRecipient',
    'SESComplaint',
    'ComplainedRecipient',
)

class SESStat(models.Model):
    date = models.DateField(unique=True, db_index=True)
    delivery_attempts = models.PositiveIntegerField()
    bounces = models.PositiveIntegerField()
    complaints = models.PositiveIntegerField()
    rejects = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'SES Stat'
        ordering = ['-date']

    def __unicode__(self):
        return self.date.strftime("%Y-%m-%d")

class SESNotificationBase(models.Model):
    """
    A base abstract model containing common fields for
    SES notification messages. SES notification messages
    are routed to the app via Amazon SNS and delivered as
    a JSON encoded POST request.
    """
    timestamp = models.DateTimeField(
        verbose_name=_("Timestamp"), 
        help_text=_("""The time at which the original message was sent in """
                    """the ISO8601 format.""")
    )
    message_id = models.CharField(
        verbose_name=_("Message Id"),
        max_length=256,
        help_text=_("""A unique ID for the original message. This is the ID """
                    """that was returned to you by Amazon SES when you sent """
                    """the original message.""")
    )
    source = models.CharField(
        verbose_name=_("Source"),
        max_length=256,
        help_text=_("""The email address from which the original message was """
                    """sent (the envelope MAIL FROM address).""")
    )
    destination = models.TextField(
        verbose_name=_("Destination"),
        help_text=_("""A list of email addresses that were recipients of the """
                    """original mail.""")
    )
    raw_sns_message = models.TextField(
        verbose_name=_("Raw SNS Message"),
        help_text=_("The raw SNS JSON message.")
    )

    class Meta:
        abstract = True

class SESBounce(SESNotificationBase):
    """
    Log data of SES email bounce messages.
    """
    BOUNCE_TYPES = (
        ('Undetermined', 'Undetermined'),
        ('Permanent', 'Permanent'),
        ('Transient', 'Transient'),
    )

    BOUNCE_SUB_TYPES = (
        # Undetermined
        ('Undetermined', 'Undetermined'), 

        # Permanent
        ('General', 'General'), # also Transient
        ('NoEmail', 'No Email'),

        # Transient
        ('MailboxFull', 'Mailbox Full'),
        ('MessageToolarge', 'Message Too Large'),
        ('ContentRejected', 'Content Rejected'),
        ('AttachmentRejected', 'Attachment Rejected'),
    )

    bounce_type = models.CharField(
        verbose_name=_("Bounce Type"),
        choices=BOUNCE_TYPES,
        max_length=20,
        help_text=_("""The type of bounce, as determined by Amazon SES. """
                    """For more information, see """
                    """<a href=\"http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/NotificationContents.html#BounceTypes\">Bounce Types</a>.""")
    )
    bounce_subtype = models.CharField(
        verbose_name=_("Bounce Sub-Type"),
        choices=BOUNCE_SUB_TYPES,
        max_length=20,
        help_text=_("The subtype of the bounce, as determined by Amazon SES. """
                    """For more information, see """
                    """<a href=\"http://docs.amazonwebservices.com/ses/latest/DeveloperGuide/NotificationContents.html#BounceTypes\">Bounce Types</a>.""")
    )
    bounce_timestamp = models.DateTimeField(
        verbose_name=_("Bounce Timestamp"), 
        help_text=_("""The date and time at which the bounce was sent """
                    """(in ISO8601 format). Note that this is the time at """
                    """which the feedback was sent by the ISP, and not the """
                    """time at which it was received by Amazon SES.""")
    )
    feedback_id = models.CharField(_("Feedback Id"), max_length=256,
                                   help_text=_("A unique ID for the bounce."))

    class Meta:
        verbose_name = _('SES Bounced Message')
        ordering = ['-timestamp']

    def __unicode__(self):
        return u"SESBounce(%s)" % self.feedback_id

class BouncedRecipient(models.Model):
    """
    A Bounced Message Recipient
    """
    bounce = models.ForeignKey(SESBounce, related_name="recipients")

    email_address = models.EmailField(
        verbose_name=_("Email Address"),
        help_text=_("""The value of the Status field from the DSN. This is """
                    """the per-recipient transport-independent status code """
                    """that indicates the delivery status of the message.""")
    )
    action = models.CharField(
        verbose_name=_("Action"),
        max_length=256,
        null=True,
        blank=True,
        help_text=_("""The value of the Action field from the DSN. This """
                    """indicates the action performed by the Reporting-MTA """
                    """as a result of its attempt to deliver the message to """
                    """this recipient.""")
    )
    diagnostic_code = models.CharField(
        verbose_name=_("Diagnostic Code"),
        max_length=256,
        null=True,
        blank=True,
        help_text=_("""The status code issued by the reporting MTA. This is """
                    """the value of the Diagnostic-Code field from the DSN. """
                    """This field may be absent in the DSN (and therefore """
                    """also absent in the JSON).""")
    )

    class Meta:
        verbose_name = _('SES Bounced Recipient')

    def __unicode__(self):
        return self.email_address

class SESComplaint(SESNotificationBase):
    """
    An SES Complaint
    """
    complaint_timestamp = models.DateTimeField(
        verbose_name=_("Complaint Timestamp"), 
        help_text=_("""The date and time at which the bounce was sent """
                    """(in ISO8601 format). Note that this is the time at """
                    """which the feedback was sent by the ISP, and not the """
                    """time at which it was received by Amazon SES.""")
    )
    feedback_id = models.CharField(
        verbose_name=_("Feedback Id"),
        max_length=256,
        help_text=_("A unique ID for the complaint.")
    )

    user_agent = models.CharField(
        verbose_name=_("User Agent"),
        max_length=256,
        null=True,
        blank=True,
        help_text=_("""The value of the User-Agent field from the feedback """
                    """report. This indicates the name and version of the """
                    """system that generated the report.""")
    )
    complaint_feedback_type = models.CharField(
        verbose_name=_("Complaint Feedback Type"),
        max_length=256,
        null=True,
        blank=True,
        help_text=_("""The value of the Feedback-Type field from the """
                    """feedback report received from the ISP. This contains """
                    """the type of feedback.""")
    )
    arrival_date = models.DateTimeField(
        verbose_name=_("Arrival Date"),
        null=True,
        blank=True,
        help_text=_("""The value of the Arrival-Date or Received-Date field """
                    """from the feedback report (in ISO8601 format). This """
                    """field may be absent in the report (and therefore also """
                    """absent in the JSON).""")
    )

    class Meta:
        verbose_name = _('SES Complaint')
        ordering = ['-timestamp']

    def __unicode__(self):
        return "SESComplaint(%s)" % self.feedback_id 

class ComplainedRecipient(models.Model):
    """
    Recipient responsible for the complaint
    """
    complaint = models.ForeignKey(SESComplaint, related_name="recipients")
    email_address = models.EmailField(_("Email Address"), null=True, blank=True,
        help_text=_("The email address of the recipient."))

    class Meta:
        verbose_name = _('SES Complained Recipient')

    def __unicode__(self):
        return self.email_address
