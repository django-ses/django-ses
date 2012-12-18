
from django.dispatch import Signal

bounce_received = Signal(providing_args=["mail_obj", "bounce_obj"])

complaint_received = Signal(providing_args=["mail_obj", "complaint_obj"])
