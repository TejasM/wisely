from __future__ import division
from datetime import date
import json

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def convertDatetimeToString(o):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    return o.strftime("%s %s" % (DATE_FORMAT, TIME_FORMAT))


class BaseModel(models.Model):
    created = models.DateTimeField(default=timezone.now())
    last_updated = models.DateTimeField(default=timezone.now(), auto_now=True)

    class Meta:
        abstract = True


class Course(BaseModel):
    title = models.CharField(max_length=400)
    course_id = models.IntegerField(default=None, null=True, blank=True)
    course_link = models.CharField(max_length=1000, default="")
    quiz_link = models.CharField(max_length=1000, default="")
    calender_link = models.CharField(max_length=1000, default="")
    info_link = models.CharField(max_length=1000, default="")
    description = models.CharField(max_length=10000, default="")
    start_date = models.DateField(default=None, null=True, blank=True)
    end_date = models.DateField(default=None, null=True, blank=True)
    image_link = models.CharField(default="", max_length=10000)

    def __unicode__(self):
        return self.title

    def get_amount_progress(self):
        percentage = 50
        if self.end_date is not None and self.start_date is not None:
            if self.end_date > timezone.now().date():
                percentage = (timezone.now().date() - self.start_date).days / (
                    (self.end_date - self.start_date).days) * 100
            else:
                percentage = 100

        return percentage

    @property
    def is_done(self):
        if date.today() > self.end_date:
            return True
        return False


class CourseraProfile(BaseModel):
    user = models.OneToOneField(User)
    courses = models.ManyToManyField(Course)
    username = models.CharField(max_length=100, default="", unique=True)
    password = models.CharField(max_length=100, default="")
    counted_as_completed = models.CommaSeparatedIntegerField(default='', blank=True, max_length=200)
    incorrect_login = models.BooleanField(default=False)


class UserProfile(BaseModel):
    user = models.OneToOneField(User)
    picture = models.ImageField(upload_to='profile_images', null=True)
    current_city = models.CharField(max_length=32, null=True)

    MALE = 'M'
    FEMALE = 'F'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER, null=True)

    birthday = models.DateField(null=True, blank=True)
    headline = models.TextField(null=True, blank=True, max_length=64)
    about_me = models.TextField(null=True, blank=True, max_length=500)
    website = models.URLField(null=True, blank=True)


class Quiz(BaseModel):
    heading = models.CharField(max_length=400, default="")
    course = models.ForeignKey(Course)
    deadline = models.DateTimeField(null=True, default=None)
    hard_deadline = models.DateTimeField(null=True, default=None)

    def __unicode__(self):
        return self.heading


class Progress(BaseModel):
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