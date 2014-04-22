from django.utils import timezone
from django.db import models

from users.models import Course, BaseModel, UserProfile


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

    def get_aim(self):
        return self.aim*100

    def get_actual_mark(self):
        if self.actual_mark:
            return self.actual_mark*100
        else:
            return 0


class Reward(BaseModel):
    money = models.DecimalField(max_digits=8, decimal_places=2)
    user = models.ForeignKey(UserProfile)
    pledge = models.ForeignKey(Pledge, default=None, null=True, blank=True)
    collected = models.BooleanField(default=False)


class Follower(BaseModel):
    pledge = models.ForeignKey(Pledge)
    email = models.EmailField(default='', blank=True)