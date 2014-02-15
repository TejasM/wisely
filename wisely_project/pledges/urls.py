__author__ = 'Cheng'

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
                       # /pledges/
                       url(r'^$', views.index, name='index'),
                       url(r'^create/$', views.create, name='create'),
                       # /pledges/23
                       url(r'^(?P<pledge_id>\d+)/$', views.detail, name='detail'),
                       url(r'^follow/(?P<user_id>\d+)/$', views.follow, name='follow'),
                       url(r'^finish/(?P<user_id>\d+)/$', views.finish, name='finish'),
                       url(r'^success/(?P<pledge_id>\d+)/$', views.congrats, name='congrats'),
                       url(r'^already/(?P<user_id>\d+)/$', views.already, name='already'),
                       url(r'^share/(?P<pledge_id>\d+)/$', views.share, name='share'),
                       # /pledges/23/
                       url(r'^(?P<pledge_id>\d+)/results/$', views.results, name='results'),
)
