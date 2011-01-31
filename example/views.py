from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.core.mail import send_mail, EmailMessage

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
            <label for="message">HTML:</label>
            <input type="checkbox" name="html-message" id="html-message" />
            <br />
            <input type="submit" value="Send Email" />
        </form>
    """.format(send_email_url=reverse('send-email')))

def send_email(request):
    try:
        subject = request.POST['subject']
        message = request.POST['message']
        from_email = request.POST['from']
        html_message = bool(request.POST.get('html-message', False))
        recipient_list = [request.POST['to']]

        email = EmailMessage(subject, message, from_email, recipient_list)
        if html_message:
            email.content_subtype = 'html'
        email.send()
    except KeyError:
        return HttpResponse('Please fill in all fields')

    return HttpResponse('Email sent :)')

