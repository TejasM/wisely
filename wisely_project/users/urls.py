import views

__author__ = 'tmehta'

from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^login/$', views.login_user, name='login'),
                       url(r'^logout/$', views.logout_user, name='logout'),
                       url(r'^signup/$', views.signup, name='sign-up'),
                       url(r'^index/$', views.index_alt, name='index'),
                       url(r'^index/alt$', views.index_alt, name='index_alt'),
                       url(r'^check_updated/$', views.check_updated, name='check_update'),
                       url(r'^force_updated/$', views.force_updated, name='force_update'),
                       url(r'^profile/$', views.profile, name='profile'),
                       url(r'^edit_profile/$', views.edit_profile, name='edit_profile'),
                       url(r'^profile/(?P<user_id>\w+)/$', views.public_profile, name='public_profile'),
                       url(r'^news/$', views.news, name='news'),
                       url(r'^compose/$', views.compose, name='compose'),
                       url(r'^reply/$', views.reply, name='reply'),
                       url(r'^follow/$', views.follow, name='follow'),
                       url(r'^get_course_stats/$', views.get_course_stats, name='get_course_stats'),
                       url(r'^contact_us/$', views.contact_us, name='contact_us'),
)