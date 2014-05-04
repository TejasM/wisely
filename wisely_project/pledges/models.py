from django.contrib import admin
from django.utils import timezone
from django.db import models

from users.models import Course, BaseModel, UserProfile, Progress, convert_to_percentage
from datetime import date


class Pledge(BaseModel):
    user = models.ForeignKey(UserProfile)
    course = models.ForeignKey(Course)
    money = models.DecimalField(max_digits=8, decimal_places=2)
    pledge_date = models.DateTimeField('date pledged', default=timezone.now())
    complete_date = models.DateTimeField('date completed', null=True)
    is_active = models.BooleanField(default=True)
    is_complete = models.BooleanField(default=False)
    aim = models.FloatField(default=0.50)
    actual_mark = models.FloatField(default=None, null=True, blank=True)
    charge = models.CharField(default="", max_length=1000)
    pledge_end_date = models.DateField(default=timezone.now(), null=True)

    def get_full_stats(self):
        grades = Progress.objects.filter(quiz__course=self.course, user=self.user).values_list('score', flat=True)
        if grades:
            grades = [convert_to_percentage(x) for x in grades]
            grades = sum(grades)/len(grades)
        else:
            grades = 0
        print "Course:", self.course
        print "Current Grade:", grades
        print "Current Aim", self.aim
        print "End date", self.pledge_end_date
        return

    def get_aim(self):
        return self.aim*100

    def get_actual_mark(self):
        if self.actual_mark:
            return self.actual_mark*100
        else:
            return 0

    def get_amount_progress(self):
        percentage = 0
        if self.pledge_end_date is not None and self.pledge_date is not None:
            if self.pledge_end_date > timezone.now().date():
                percentage = (timezone.now().date() - self.pledge_date).days / (
                    (self.pledge_end_date - self.pledge_date).days) * 100
            else:
                percentage = 100
        elif self.pledge_date is None and self.pledge_date is not None:
            percentage = 100
        return percentage

    @property
    def is_done(self):
        if self.pledge_end_date is not None:
            if date.today() > self.pledge_end_date:
                return True
        return False

    def __unicode__(self):
        return str(self.aim) + " " + self.course + " " + self.user.user.first_name + " " + self.user.user.last_name


admin.site.register(Pledge)


class Reward(BaseModel):
    money = models.DecimalField(max_digits=8, decimal_places=2)
    user = models.ForeignKey(UserProfile)
    pledge = models.ForeignKey(Pledge, default=None, null=True, blank=True)
    collected = models.BooleanField(default=False)


class Follower(BaseModel):
    pledge = models.ForeignKey(Pledge)
    email = models.EmailField(default='', blank=True)