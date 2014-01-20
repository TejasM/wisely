from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from settings import production

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', TemplateView.as_view(template_name='base.html')),

                       # Examples:
                       # url(r'^$', 'wisely_project.views.home', name='home'),
                       # url(r'^wisely_project/', include('wisely_project.foo.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       url(r'^admin/', include(admin.site.urls)),
                       url(r"^payments/", include("payments.urls")),
                       url(r'^users/', include('users.urls', namespace="users")),
                       url(r'', include('social_auth.urls')),
                       url(r'^pledges/', include('pledges.urls', namespace="pledges")),
)

if not production.DEBUG:
    urlpatterns += patterns('',
                            (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                             {'document_root': production.STATIC_ROOT}),
    )