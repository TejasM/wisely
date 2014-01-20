from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from users.models import Course

__author__ = 'Cheng'

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from models import Pledge


@login_required
def index(request):
    all_pledges_list = Pledge.objects.all().order_by('-pledge_date')
    context = {'all_pledges_list': all_pledges_list}
    return render(request, 'pledges/index.html', context)


@login_required
def detail(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    return render(request, 'pledges/detail.html', {'pledge': pledge})


@login_required
def results(request, poll_id):
    return HttpResponse("You're looking at the results of pledge %s." % poll_id)


@login_required
def create(request):
    if request.method == "POST":
        pledge = Pledge.objects.create(user=request.user.userprofile, course=Course.objects.get(pk=int(request.POST['course'])),
                                       money=int(float(request.POST['money'])), active=True)
        return redirect(reverse('pledges:detail', args=(pledge.id,)))
    return render(request, 'pledges/create.html')


@login_required
def edit(request, pledge_id):
    try:
        pledge = Pledge.objects.get(pk=pledge_id)
    except Pledge.DoesNotExist:
        return redirect(reverse('user:index'))
    if request.method == "POST":
        pledge = Pledge.objects.get(pk=pledge_id)
        pledge.course = Course.objects.get(pk=int(request.POST['course']))
        pledge.money = int(float(request.POST['money']))
        pledge.save()
        return redirect(reverse('pledges:detail', args=(pledge.id,)))
    return render(request, 'pledges/edit.html', {'pledge': pledge})