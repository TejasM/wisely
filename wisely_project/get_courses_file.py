import sys
import os
import traceback

from django import db

sys.path.append('/root/wisely/wisely_project/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'wisely_project.settings.production'

from django.db.models import F
from django.utils import timezone
from users.tasks import get_coursera_courses, get_edx_courses, get_udemy_courses

__author__ = 'tmehta'

from users.models import CourseraProfile, EdxProfile, UdemyProfile

while True:
    try:
        for connection in db.connections.all():
            if len(connection.queries) > 100:
                db.reset_queries()
        for user in CourseraProfile.objects.filter(last_updated__lt=F('user__last_login')):
            if user.username != '':
                print "Start coursera"
                get_coursera_courses(user)
                user.last_updated = timezone.now()
                user.save()
        for user in EdxProfile.objects.filter(last_updated__lt=F('user__last_login')):
            if user.email != '':
                print "Start edx"
                get_edx_courses(user)
                user.last_updated = timezone.now()
                user.save()
        for user in UdemyProfile.objects.filter(last_updated__lt=F('user__last_login')):
            if user.email != '':
                print "Start udemy"
                get_udemy_courses(user)
                user.last_updated = timezone.now()
                user.save()

    except Exception as e:
        print traceback.format_exc()
