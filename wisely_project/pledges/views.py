from __future__ import division
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
import stripe

from users.models import Course




__author__ = 'Cheng'

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from models import Pledge, Follower
import wisely_project.settings.base as settings


@login_required
def index(request):
    all_pledges_list = Pledge.objects.filter(user=request.user.userprofile).order_by('-pledge_date')
    list_projections = []
    for pledge in all_pledges_list:
        bonus_reward = calculate_bonus_rewards(pledge)
        projected_rewards = calculate_projected_rewards(pledge)
        actual_full_projection = projected_rewards + min(bonus_reward, projected_rewards / 2)
        list_projections.append((bonus_reward, projected_rewards, actual_full_projection))
    context = {'all_pledges_list': all_pledges_list, 'all_projections': list_projections}
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
                    amount=int(float(pledge.money)) * 100,  # amount in cents, again
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


def calculate_projected_rewards(pledge):
    all_pledges = Pledge.objects.filter(course=pledge.course)
    total_pool = reduce(lambda x, y: x + y, map(lambda x: x.money, all_pledges))
    probable_pool = 0.2 * float(total_pool)
    average_aim = reduce(lambda x, y: x + y, map(lambda x: x.aim, all_pledges)) / all_pledges.count()
    probable_num_rewarded = all_pledges.count() * 0.8
    probable_earning = (1 + (pledge.aim - average_aim) / 2) * probable_pool / probable_num_rewarded
    return probable_earning


def calculate_pooled_average(course):
    all_pledges = Pledge.objects.filter(course=course)
    if all_pledges:
        total_pool = reduce(lambda x, y: x + y, map(lambda x: x.money, all_pledges))
        probable_pool = 0.2 * float(total_pool)
        average_aim = reduce(lambda x, y: x + y, map(lambda x: x.aim, all_pledges)) / all_pledges.count()
        probable_num_rewarded = all_pledges.count() * 0.8
        return probable_pool / probable_num_rewarded, average_aim
    else:
        return 0, 0


def calculate_bonus_rewards(pledge):
    followers = Follower.objects.filter(pledge=pledge)
    return followers.count()


@login_required
def share(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    if request.session.get('onboarding', '') != '':
        request.session.pop('onboarding')
        return render(request, 'pledges/share.html', {'pledge': pledge, 'form': True})
    return render(request, 'pledges/share.html', {'pledge': pledge})


def follow(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    if (
        request.user.is_authenticated() and request.user.userprofile != pledge.user) or not request.user.is_authenticated():
        if request.method == "POST":
            email = request.POST.get('email', '')
            if email != '':
                if Follower.objects.filter(email=email, pledge=pledge).count() == 0:
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


def congrats(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id, is_complete=True)
    return render(request, 'pledges/success.html', {'pledge': pledge})


def already(request, pledge_id):
    pledge = get_object_or_404(Pledge, pk=pledge_id)
    return render(request, 'pledges/finish.html', {'pledge': pledge, 'good': False})


@login_required
def results(request, poll_id):
    return HttpResponse("You're looking at the results of pledge %s." % poll_id)


@login_required
def create(request):
    if request.method == "POST":
        if request.POST.get('onboarding', '') != '':
            pledge = Pledge.objects.create(user=request.user.userprofile,
                                           course=Course.objects.get(pk=int(request.POST['course'])),
                                           money=int(float(request.POST['money'].replace(',', ''))), is_active=False,
                                           aim=float(request.POST['aim'].replace('%', '')) / 100)
            return redirect(reverse('pledges:detail', args=(pledge.id,)))
        else:
            token = request.POST.get('stripeToken', '')
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                stripe.Charge.create(
                    amount=int(float(request.POST['money'].replace(',', ''))) * 100,  # amount in cents, again
                    currency="cad",
                    card=token,
                    description=request.user.username,
                )
                pledge = Pledge.objects.create(user=request.user.userprofile,
                                               course=Course.objects.get(pk=int(request.POST['course'])),
                                               money=int(float(request.POST['money'].replace(',', ''))), is_active=True,
                                               aim=float(request.POST['aim'].replace('%', '')) / 100)
            except stripe.CardError, _:
                return redirect(reverse('pledges:create'))
            return redirect(reverse('pledges:share', args=(pledge.id,)))

    other_pledgers_list = []
    projections = []
    pledged_courses = Pledge.objects.filter(user=request.user.userprofile).values_list('course_id')
    if pledged_courses:
        courses_available = request.user.courseraprofile.courses.filter(~Q(pk=pledged_courses))
    else:
        courses_available = request.user.courseraprofile.courses.all()
    for course in courses_available:
        other_pledgers_list.append(Pledge.objects.filter(~Q(user=request.user)).filter(course=course).order_by('?')[:5])
        potential, average_aim = calculate_pooled_average(course)
        projections.append((potential, average_aim, course.id))

    if request.session.get('onboarding', '') != '':
        return render(request, 'pledges/create.html',
                      {'form': True, 'wait': request.user.last_login > request.user.courseraprofile.last_updated,
                       'others': other_pledgers_list, 'courses': courses_available, 'projections': projections})
    else:
        return render(request, 'pledges/create.html', {'others': other_pledgers_list, 'courses': courses_available,
                                                       'projections': projections})