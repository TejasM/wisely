from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, render_to_response

__author__ = 'tmehta'


def index(request):
    done = request.COOKIES.get('animation', '')
    response = render_to_response('base-alt.html', {'done': done})
    response.set_cookie('animation', 'done')
    return response


def index_alt(request):
    done = request.COOKIES.get('animation', '')
    response = render_to_response('base-alt.html', {'done': done})
    response.set_cookie('animation', 'done')
    return response