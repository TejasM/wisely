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
    reward = models.FloatField(default=0)
    actual_mark = models.FloatField(default=None, null=True, blank=True)

    def get_aim(self):
        return self.aim*100

    def get_actual_mark(self):
        return self.actual_mark*100


class Follower(BaseModel):
    pledge = models.ForeignKey(Pledge)
    email = models.EmailField(default='', blank=True)