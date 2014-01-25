import views

__author__ = 'tmehta'

from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^login/$', views.login, name='login'),
                       url(r'^logout/$', views.logout_user, name='logout'),
                       url(r'^signup/$', views.signup, name='sign-up'),
                       url(r'^index/$', views.index, name='index'),
                       url(r'^check_updated/$', views.check_updated, name='check_update'),
)