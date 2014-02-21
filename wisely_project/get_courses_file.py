import sys
import os

from django import db


sys.path.append('/root/wisely/wisely_project/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'wisely_project.settings.production'

from django.db.models import F
from django.utils import timezone
from users.tasks import get_courses

__author__ = 'tmehta'

from users.models import CourseraProfile

while True:
    try:
        db.reset_queries()
        for user in CourseraProfile.objects.filter(last_updated__lt=F('user__last_login')):
            get_courses(user.user_id)
            user.last_updated = timezone.now()
            user.save()
    except Exception as e:
        print e
