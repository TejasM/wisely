import datetime
from django.core.mail import EmailMessage
from django.template import RequestContext
from django.template.loader import get_template

__author__ = 'tmehta'


def divide_timedelta(td, divisor):
    divided_seconds = td.total_seconds() / float(divisor)
    return datetime.timedelta(seconds=divided_seconds)


def send_welcome_email(request):
    try:
        email_data = {
            'user': request.user,
        }
        email_data = RequestContext(request, email_data)
        msg = create_email('email/welcome_email.html', email_data, [request.user.email])
        msg.send()
    except Exception as e:
        print e


def create_email(template, data, to_list):
    t = get_template(template)
    content = t.render(data)
    msg = EmailMessage('Welcome to Wisely', content, 'contact@projectwisely.com', to_list)
    msg.content_subtype = "html"
    return msg