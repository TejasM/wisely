import sys, os
sys.path.append('/root/wisely/wisely_project/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'wisely_project.settings.production'
from django.conf import settings

from django.db.models import F
from django.utils import timezone
from users.tasks import get_courses

__author__ = 'tmehta'

from users.models import UserProfile

for user in UserProfile.objects.filter(last_updated__lt=F('user__last_login')):
    get_courses(user.user_id)
    user.last_updated = timezone.now()
    user.save()
