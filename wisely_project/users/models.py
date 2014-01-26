import datetime
import json
from django.contrib.auth.models import User
from django.db import models


# Create your models here.
from django.utils import timezone


def convertDatetimeToString(o):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    return o.strftime("%s %s" % (DATE_FORMAT, TIME_FORMAT))


class Course(models.Model):
    title = models.CharField(max_length=400)
    course_link = models.CharField(max_length=1000, default="")
    quiz_link = models.CharField(max_length=1000, default="")

    def __unicode__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    courses = models.ManyToManyField(Course)
    coursera_username = models.CharField(max_length=100, default="")
    coursera_password = models.CharField(max_length=100, default="")
    last_updated = models.DateTimeField(default=timezone.now())


class Quiz(models.Model):
    heading = models.CharField(max_length=400, default="")
    course = models.ForeignKey(Course)
    deadline = models.DateTimeField(null=True, default=None)
    hard_deadline = models.DateTimeField(null=True, default=None)

    def __unicode__(self):
        return self.heading


class Progress(models.Model):
    user = models.ForeignKey(UserProfile)
    quiz = models.ForeignKey(Quiz)
    score = models.CharField(max_length=200, default="Pending")

    def __unicode__(self):
        if str(self.score) == 'N/A':
            if self.quiz.hard_deadline.date() < timezone.now().date():
                return "<strong>" + self.quiz.heading + "</strong>: Past Due Date"
            return "<strong>" + self.quiz.heading + "</strong> Due Date: " + convertDatetimeToString(self.quiz.deadline)
        return "<strong>" + self.quiz.heading + "</strong>: " + self.score

    def get_date(self):
        return json.dumps({'date': self.quiz.deadline.date(), 'title': self.quiz.heading})