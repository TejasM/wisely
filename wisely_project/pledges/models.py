from django.utils import timezone
from users.models import Course, UserProfile

__author__ = 'Cheng'

from django.db import models


class Pledge(models.Model):
    user = models.ForeignKey(UserProfile)
    course = models.ForeignKey(Course)
    money = models.IntegerField(default=0)
    pledge_date = models.DateTimeField('date pledged', default=timezone.now())
    complete_date = models.DateTimeField('date completed', blank=True,  default=timezone.now())
    active = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)

    def __unicode__(self):
        return self.user + "'s pledges is: " + self.money + " made on " + self.pledge_date + " for course " + self.course


class Follower(models.Model):
    pledge = models.ForeignKey(Pledge)
    email = models.EmailField(default='', blank=True)
