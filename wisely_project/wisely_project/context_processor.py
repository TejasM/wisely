from random import randint

from django.db.models import Q

from polls.models import Question
from users.models import UserProfile, CourseraProfile, EdxProfile, UdemyProfile
from wisely_project.settings import base as settings

__author__ = 'tmehta'


def async_url(request):
    return {'async_url': settings.ASYNC_BACKEND_URL}


def survey_questions(request):
    if request.user.is_authenticated():
        mooc_profile = ""
        try:
            mooc_profile = CourseraProfile.objects.get(user=request.user)
        except CourseraProfile.DoesNotExist:
            pass
        if mooc_profile == "" or mooc_profile.username == "" or mooc_profile.incorrect_login:
            try:
                mooc_profile = EdxProfile.objects.get(user=request.user)
            except EdxProfile.DoesNotExist:
                pass
            if mooc_profile == "" or mooc_profile.email == "" or mooc_profile.incorrect_login:
                try:
                    mooc_profile = UdemyProfile.objects.get(user=request.user)
                except UdemyProfile.DoesNotExist:
                    pass
                if mooc_profile == "" or mooc_profile.email == "" or mooc_profile.incorrect_login:
                    return {}

        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist as _:
            profile = UserProfile.objects.create(user=request.user)
        possible_questions = Question.objects.filter(
            ~Q(pk__in=profile.questions_answered.all().values_list('id', flat='True')))
        if possible_questions.count() > 0:
            last = possible_questions.count() - 1
            index1 = randint(0, last)
            return {'question': possible_questions[index1]}
        else:
            return {}
    return {}