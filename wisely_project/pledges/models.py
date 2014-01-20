__author__ = 'Cheng'

from django.db import models


class Pledge(models.Model):
    user = models.ForeignKey('users.UserProfile')
    course = models.ForeignKey('users.Course')
    money = models.IntegerField(default=0)
    pledge_date = models.DateTimeField('date pledged')
    complete_date = models.DateTimeField('date completed', blank=True)
    active = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)

    def __unicode__(self):
        return self.user + "'s pledges is: " + self.money + " made on " + self.pledge_date + " for course " + self.course



