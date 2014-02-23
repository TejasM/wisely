__author__ = 'Cheng'

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
                       url(r'^answer/(?P<question_id>\w+)/$', views.answer_question, name='anspoll'),
)
