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
    course_link = models.CharField(max_length=1000, default="")
    quiz_link = models.CharField(max_length=1000, default="")

    def __unicode__(self):
        return self.title


class CourseraProfile(BaseModel):
    user = models.OneToOneField(User)
    courses = models.ManyToManyField(Course)
    username = models.CharField(max_length=100, default="")
    password = models.CharField(max_length=100, default="")


class UserProfile(BaseModel):
    user = models.OneToOneField(User)
    picture = models.ImageField(upload_to='profile_images', null=True)
    location = models.CharField(max_length=128, blank=True, default="")

    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'
    UNSPECIFIED = 'U'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (OTHER, 'Other'),
        (UNSPECIFIED, 'Unspecified'),
    )
    gender = models.CharField(max_length=1, choices=GENDER, default=UNSPECIFIED)

    birthday = models.DateField(null=True, blank=True)
    about_me = models.TextField(null=True, blank=True, max_length=500)
    website = models.URLField(null=True, blank=True)
    linkedIn = models.URLField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)
    google_plus = models.URLField(null=True, blank=True)
    github = models.URLField(null=True, blank=True)


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