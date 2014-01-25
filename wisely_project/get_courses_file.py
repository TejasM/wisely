import sys, os

sys.path.append('/root/wisely/wisely_project/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'wisely_project.settings.production'
from django.conf import settings

from django.db.models import F
from django.utils import timezone
from users.tasks import get_courses, CourseraScraper

__author__ = 'tmehta'

from users.models import UserProfile

scraper = CourseraScraper()

while True:
    for user in UserProfile.objects.filter(last_updated__lt=F('user__last_login')):
        try:
            get_courses(user.user_id, scraper)
            user.last_updated = timezone.now()
            user.save()
        except:
            pass

scraper.driver.close()
scraper.display.stop()