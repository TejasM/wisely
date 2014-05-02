import urllib
import urllib2
from django.contrib.auth.models import User
from django.db import models
from django.conf import settings


def send_event(event_type, event_data):
    to_send = {
        'event': event_type,
        'data': event_data
    }
    urllib2.urlopen(settings.ASYNC_BACKEND_URL, urllib.urlencode(to_send))


class Session(models.Model):
    public = models.BooleanField(default=False)
    current_users = models.ManyToManyField(User, related_name='current_user')
    all_users = models.ManyToManyField(User, related_name='all_users')
    live = models.BooleanField(default=True)
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=200, default='')
    audio = models.BooleanField(default=False)
    video = models.BooleanField(default=False)
    coding = models.BooleanField(default=False)
    code = models.CharField(max_length=100000, default="")


class ChatLog(models.Model):
    session = models.ForeignKey(Session)


class Message(models.Model):
    user = models.ForeignKey(User)
    message = models.CharField(max_length=10000, default="")
    log = models.ForeignKey(ChatLog)