from __future__ import division
from datetime import date
from fractions import Fraction
import json
import locale
from django.contrib import admin

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from polls.models import Question


def convertDatetimeToString(o):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    return o.strftime("%s %s" % (DATE_FORMAT, TIME_FORMAT))


def convert_to_percentage(string):
    try:
        num = float(string)
    except ValueError:
        try:
            num = locale.atof(string)
        except ValueError:
            try:
                num = float(Fraction(string))
            except ValueError:
                try:
                    clean = string.replace(' ', '')
                    clean = clean.split('/')
                    if len(clean) == 2:
                        num = float(Fraction(int(float(clean[0]) * 100), int(float(clean[1]) * 100)))
                    else:
                        num = 0
                except ValueError:
                    return 0
            except ZeroDivisionError:
                return 0
    return num * 100


class BaseModel(models.Model):
    created = models.DateTimeField(default=timezone.now())
    last_updated = models.DateTimeField(default=timezone.now(), auto_now=True)

    class Meta:
        abstract = True


class Course(BaseModel):
    title = models.CharField(max_length=400)
    course_id = models.CharField(default=None, null=True, blank=True, max_length=100)
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
        percentage = 0
        if self.end_date is not None and self.start_date is not None:
            if self.end_date > timezone.now().date():
                percentage = (timezone.now().date() - self.start_date).days / (
                    (self.end_date - self.start_date).days) * 100
            else:
                percentage = 100
        elif self.start_date is None and self.end_date is not None:
            percentage = 100
        return percentage

    @property
    def is_done(self):
        if self.end_date is not None:
            if date.today() > self.end_date:
                return True
        return False


class CourseraProfile(BaseModel):
    user = models.OneToOneField(User)
    courses = models.ManyToManyField(Course)
    username = models.CharField(max_length=100, default="")
    password = models.CharField(max_length=100, default="")
    counted_as_completed = models.CommaSeparatedIntegerField(default='', blank=True, max_length=200)
    incorrect_login = models.BooleanField(default=False)


class EdxProfile(BaseModel):
    user = models.OneToOneField(User)
    courses = models.ManyToManyField(Course)
    email = models.CharField(max_length=100, default="")
    password = models.CharField(max_length=100, default="")
    counted_as_completed = models.CommaSeparatedIntegerField(default='', blank=True, max_length=200)
    incorrect_login = models.BooleanField(default=False)


class UdemyProfile(BaseModel):
    user = models.OneToOneField(User)
    courses = models.ManyToManyField(Course)
    email = models.CharField(max_length=100, default="")
    password = models.CharField(max_length=100, default="")
    counted_as_completed = models.CommaSeparatedIntegerField(default='', blank=True, max_length=200)
    incorrect_login = models.BooleanField(default=False)


class UserProfile(BaseModel):
    user = models.OneToOneField(User)
    picture = models.ImageField(upload_to='profile_images', null=True)
    current_city = models.CharField(max_length=32, null=True)
    questions_answered = models.ManyToManyField(Question)
    last_forced = models.DateTimeField(default=None, null=True, blank=True)
    connections = models.ManyToManyField(User, related_name="connections")
    never_updated = models.BooleanField(default=True)
    customer_id = models.CharField(max_length=1000, default="")

    MALE = 'M'
    FEMALE = 'F'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER, null=True)
    follows = models.ManyToManyField('self', related_name='following', symmetrical=False)
    birthday = models.DateField(null=True, blank=True)
    headline = models.TextField(null=True, blank=True, max_length=64)
    about_me = models.TextField(null=True, blank=True, max_length=500)
    website = models.URLField(null=True, blank=True)


class CourseraInline(admin.TabularInline):
    model = CourseraProfile
    exclude = ('password',)


class UdemyInline(admin.TabularInline):
    model = UdemyProfile
    exclude = ('password',)


class EdxInline(admin.TabularInline):
    model = EdxProfile
    exclude = ('password',)


class UserCourses(admin.ModelAdmin):
    fields = ['email',]
    list_display = ('email', 'get_courses')
    inlines = [CourseraInline, EdxInline, UdemyInline]

    def get_courses(self, obj):
        courses = ""
        if obj.edxprofile:
            for x in obj.edxprofile.courses.all():
                courses += x.title + '\n'
        if obj.courseraprofile:
            for x in obj.courseraprofile.courses.all():
                courses += x.title + '\n'
        if obj.udemyprofile:
            for x in obj.udemyprofile.courses.all():
                courses += x.title + '\n'
        return courses


#admin.site.register(User, UserCourses)


class Quiz(BaseModel):
    heading = models.CharField(max_length=400, default="")
    course = models.ForeignKey(Course)
    deadline = models.DateTimeField(null=True, default=None)
    hard_deadline = models.DateTimeField(null=True, default=None)
    quizid = models.CharField(max_length=100, default="")

    def __unicode__(self):
        return self.heading


class Invitees(models.Model):
    email_address = models.EmailField(default="")
    name = models.CharField(max_length=500, default="")
    uid = models.CharField(default='', max_length=500)
    social_media = models.CharField(default='facebook', max_length=100)
    user_from = models.ForeignKey(UserProfile, default=None, null=True)


class Progress(BaseModel):
    user = models.ForeignKey(UserProfile)
    quiz = models.ForeignKey(Quiz)
    score = models.CharField(max_length=200, default="Pending")

    def __unicode__(self):
        if str(self.score) == 'N/A':
            if self.quiz.hard_deadline.date() < timezone.now().date():
                return "<strong style='font-size=1rem'>" + self.quiz.heading + "</strong>:<br> Past Due Date"
            return "<strong style='font-size=1rem'>" + self.quiz.heading + "</strong><br> Due Date: " + convertDatetimeToString(
                self.quiz.deadline)
        return "<strong style='font-size=1rem'>" + self.quiz.heading + "</strong>:<br> " + self.score

    def get_date(self):
        return json.dumps({'date': self.quiz.deadline.date(), 'title': self.quiz.heading})

    def parse_to_percentage(self):
        return convert_to_percentage(self.score)


admin.site.register(Course)