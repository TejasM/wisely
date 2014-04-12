from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from settings import production
from wisely_project import view

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', view.index),
                       url(r'^alt$', TemplateView.as_view(template_name='base-alt.html')),
                       url(r'^main$', view.index),
                       url(r'^learn-more$', TemplateView.as_view(template_name='learn-more.html')),
                       url(r'^faq$', TemplateView.as_view(template_name='faq.html')),
                       url(r'^more$', TemplateView.as_view(template_name='more-coming.html')),
                       # Examples:
                       # url(r'^$', 'wisely_project.views.home', name='home'),
                       # url(r'^wisely_project/', include('wisely_project.foo.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       url(r'^admin/', include(admin.site.urls)),
                       url(r"^payments/", include("payments.urls")),
                       url(r'^users/', include('users.urls', namespace="users")),
                       url(r'^polls/', include('polls.urls', namespace="polls")),
                       url(r'^session/', include('studyroom.urls', namespace="studyroom")),
                       url(r'', include('social_auth.urls')),
                       url(r'^pledges/', include('pledges.urls', namespace="pledges")),
                       url(r'^blog/', include('cms.urls')),
                       url('activity/', include('actstream.urls')),
)

if not production.DEBUG:
    urlpatterns += patterns('',
                            (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                             {'document_root': production.STATIC_ROOT}),
    )