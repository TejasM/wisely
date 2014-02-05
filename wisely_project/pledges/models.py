from django.utils import timezone
from django.db import models

from users.models import Course, BaseModel, User


class Pledge(BaseModel):
    user = models.ForeignKey(User)
    course = models.ForeignKey(Course)
    money = models.DecimalField(max_digits=8, decimal_places=2)
    pledge_date = models.DateTimeField('date pledged', default=timezone.now())
    complete_date = models.DateTimeField('date completed', null=True)
    is_active = models.BooleanField(default=True)
    is_complete = models.BooleanField(default=False)


class Follower(BaseModel):
    pledge = models.ForeignKey(Pledge)
    email = models.EmailField(default='', blank=True)