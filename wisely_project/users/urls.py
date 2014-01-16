import views

__author__ = 'tmehta'

from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^login/$', views.login, name='login'),
                       url(r'^index/$', views.index, name='index'),
)