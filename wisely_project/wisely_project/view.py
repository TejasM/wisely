from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext
from social.backends.google import GooglePlusAuth
from settings.base import SOCIAL_AUTH_GOOGLE_PLUS_KEY

__author__ = 'tmehta'


def index(request):
    done = request.COOKIES.get('animation', '')
    plus_scope = ' '.join(GooglePlusAuth.DEFAULT_SCOPE)
    plus_id = SOCIAL_AUTH_GOOGLE_PLUS_KEY
    response = render_to_response('base-alt.html',
                                  {'done': done, 'user': request.user, 'plus_scope': plus_scope, 'plus_id': plus_id},
                                  context_instance=RequestContext(request))
    response.set_cookie('animation', 'done')
    return response


def index_alt(request):
    done = request.COOKIES.get('animation', '')
    plus_scope = ' '.join(GooglePlusAuth.DEFAULT_SCOPE)
    plus_id = SOCIAL_AUTH_GOOGLE_PLUS_KEY
    response = render_to_response('base-alt.html',
                                  {'done': done, 'user': request.user, 'plus_scope': plus_scope, 'plus_id': plus_id},
                                  context_instance=RequestContext(request))
    response.set_cookie('animation', 'done')
    return response