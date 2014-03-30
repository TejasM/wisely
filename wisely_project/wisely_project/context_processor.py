from random import randint
from django.db.models import Q
from polls.models import Question
from users.models import UserProfile, CourseraProfile, EdxProfile
from wisely_project.settings import base as settings
__author__ = 'tmehta'


def async_url(request):
    return {'async_url': settings.ASYNC_BACKEND_URL}


def survey_questions(request):
    if request.user.is_authenticated():
        try:
            coursera_profile = CourseraProfile.objects.get(user=request.user)
            if coursera_profile.username == "" or coursera_profile.incorrect_login:
                try:
                    edxprofile = EdxProfile.objects.get(user=request.user)
                    if edxprofile.email == "" or edxprofile.incorrect_login:
                        return {}
                except EdxProfile.DoesNotExist:
                    return {}
        except CourseraProfile.DoesNotExist:
            try:
                edxprofile = EdxProfile.objects.get(user=request.user)
                if edxprofile.email == "" or edxprofile.incorrect_login:
                    return {}
            except EdxProfile.DoesNotExist:
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