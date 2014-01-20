__author__ = 'Cheng'

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from models import Pledge


def index(request):
    all_pledges_list = Pledge.objects.all().order_by('-pledge_date')
    context = {'all_pledges_list': all_pledges_list}
    return render(request, 'pledges/index.html', context)


def detail(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    return render(request, 'pledges/detail.html', {'pledge': pledge})


def results(request, poll_id):
    return HttpResponse("You're looking at the results of pledge %s." % poll_id)


def create(request):
    return None