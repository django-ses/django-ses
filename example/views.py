from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def send_email(request):
    if request.method == 'POST':
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
    else:
        return render(request, 'send-email.html')
