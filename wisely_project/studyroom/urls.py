__author__ = 'Cheng'

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
                       url(r'^create/$', views.create_session, name='create'),
                       url(r'^goto/(?P<session_id>\w+)/$', views.go_to_session, name='gotosession'),
)
