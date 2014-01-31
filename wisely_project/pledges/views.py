from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from users.models import Course
from django.views.decorators.csrf import csrf_exempt
import stripe

__author__ = 'Cheng'

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from models import Pledge, Follower
import wisely_project.settings.base as settings


@login_required
def index(request):
    all_pledges_list = Pledge.objects.filter(user=request.user.userprofile).order_by('-pledge_date')
    context = {'all_pledges_list': all_pledges_list}
    return render(request, 'pledges/index.html', context)


@login_required
def detail(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    if request.method == "POST":
        if request.POST['type'] == 'trial':
            pledge.active = True
            pledge.save()
        else:
            token = request.POST.get('stripeToken', '')
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                stripe.Charge.create(
                    amount=int(float(pledge.money)) * 100, # amount in cents, again
                    currency="cad",
                    card=token,
                    description=request.user.username,
                )
                pledge.active = True
                pledge.save()
            except stripe.CardError, _:
                return redirect(reverse('pledges:detail', args=(pledge.id,)))
        return redirect(reverse('pledges:share', args=(pledge.id,)))
    if request.session.get('onboarding', '') != '':
        return render(request, 'pledges/detail.html', {'pledge': pledge, 'form': True})
    return redirect(reverse('pledges:share', args=(pledge.id,)))


@login_required
def share(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    if request.session.get('onboarding', '') != '':
        request.session.pop('onboarding')
        return render(request, 'pledges/share.html', {'pledge': pledge, 'form': True})
    return render(request, 'pledges/share.html', {'pledge': pledge})


def follow(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    if request.user.userprofile != pledge.user:
        if request.method == "POST":
            email = request.POST.get('email', '')
            if email != '':
                if Follower.objects.filter(email=email, pledge=pledge).count() != 0:
                    Follower.objects.create(pledge=pledge, email=email)
                else:
                    return redirect(reverse('pledges:already', args=(pledge_id,)))
            return redirect(reverse('pledges:finish', args=(pledge_id,)))
        return render(request, 'pledges/follow.html', {'pledge': pledge})
    else:
        return redirect(reverse('pledges:detail', args=(pledge_id,)))


def finish(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    return render(request, 'pledges/finish.html', {'pledge': pledge, 'good': True})


def already(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    return render(request, 'pledges/finish.html', {'pledge': pledge, 'good': False})


@login_required
def results(request, poll_id):
    return HttpResponse("You're looking at the results of pledge %s." % poll_id)


@login_required
def create(request):
    if request.method == "POST":
        if request.session.get('onboarding', '') != '' and Pledge.objects.filter(
                user=request.user.userprofile).count() == 0:
            pledge = Pledge.objects.create(user=request.user.userprofile,
                                           course=Course.objects.get(pk=int(request.POST['course'])),
                                           money=int(float(request.POST['money'].replace(',', ''))), active=False)
            return redirect(reverse('pledges:detail', args=(pledge.id,)))
        else:
            token = request.POST.get('stripeToken', '')
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                stripe.Charge.create(
                    amount=int(float(request.POST['money'].replace(',', ''))) * 100, # amount in cents, again
                    currency="cad",
                    card=token,
                    description=request.user.username,
                )
                pledge = Pledge.objects.create(user=request.user.userprofile,
                                               course=Course.objects.get(pk=int(request.POST['course'])),
                                               money=int(float(request.POST['money'].replace(',', ''))), active=True)
            except stripe.CardError, _:
                return redirect(reverse('pledges:create'))
            return redirect(reverse('pledges:share', args=(pledge.id,)))
    if request.session.get('onboarding', '') != '':
        return render(request, 'pledges/create.html',
                      {'form': True, 'wait': request.user.last_login > request.user.userprofile.last_updated})
    else:
        return render(request, 'pledges/create.html')