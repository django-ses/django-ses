from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.core.mail import send_mail

def email_form(request):
    return HttpResponse("""
        <h1>Django-SES Test</h1>
        <form method="post" action="{send_email_url}">
            <label for="from">From:</label>
            <input type="text" name="from" id="from" />
            <br />
            <label for="to">To:</label>
            <input type="text" name="to" id="to" />
            <br />
            <label for="subject">Subject:</label>
            <input type="text" name="subject" id="subject" />
            <br />
            <label for="message">Message:</label>
            <textarea name="message" id="message"></textarea>
            <br />
            <input type="submit" value="Send Email" />
        </form>
    """.format(send_email_url=reverse('send-email')))

def send_email(request):
    try:
        subject = request.POST['subject']
        message = request.POST['message']
        from_email = request.POST['from']
        recipient_list = [request.POST['to']]

        send_mail(subject, message, from_email, recipient_list)
    except KeyError:
        return HttpResponse('Please fill in all fields')

    return HttpResponse('Email sent :)')

