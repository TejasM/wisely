__author__ = 'Cheng'

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
                       # /pledges/
                       url(r'^$', views.index, name='index'),
                       url(r'^create/$', views.create, name='create'),
                       # /pledges/23
                       url(r'^(?P<pledge_id>\d+)/$', views.detail, name='detail'),
                       # /pledges/23/
                       url(r'^(?P<pledge_id>\d+)/results/$', views.results, name='results'),
)
