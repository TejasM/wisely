from __future__ import division
from datetime import datetime
import logging
import md5
import urllib
import urllib2
import json

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import requests
import stripe

from users.models import Course, UserProfile, EdxProfile, CourseraProfile, UdemyProfile
from users.utils import divide_timedelta


__author__ = 'Cheng'

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from models import Pledge, Follower, Reward
from actstream import action
from django.conf import settings


logger = logging.getLogger(__name__)


def mass_pay(email, amt):
    unique_id = str(md5.new(str(datetime.now())).hexdigest())
    params = {
        'USER': 'business1_api1.projectwisely.com',
        'PWD': '1395005281',
        'SIGNATURE': 'An5ns1Kso7MWUdW4ErQKJJJ4qi4-AMAr6-lmKHkZgOtMWnRRPehMl81N',
        'VERSION': '2.3',
        'EMAILSUBJECT': 'Here is your reward',
        'METHOD': "MassPay",
        'RECEIVERTYPE': "EmailAddress",
        'L_AMT0': amt,
        'CURRENCYCODE': 'USD',
        'L_UNIQUE0': unique_id,
        'L_NOTE0': 'Here is your reward',
        'L_EMAIL0': email,
    }
    params_string = urllib.urlencode(params)
    response = urllib2.urlopen("https://api-3t.sandbox.paypal.com/nvp", params_string).read()
    response_tokens = {}
    for token in response.split('&'):
        response_tokens[token.split("=")[0]] = token.split("=")[1]
    for key in response_tokens.keys():
        response_tokens[key] = urllib2.unquote(response_tokens[key])
    return response_tokens


@login_required
def index(request):
    all_pledges_list = Pledge.objects.filter(user=request.user.userprofile).order_by('-pledge_date')
    list_projections = []
    if request.method == "POST":
        try:
            pledge = Pledge.objects.get(pk=request.POST['pledge-id'])
        except Pledge.DoesNotExist:
            messages.error(request, 'Something really wrong happened')
            return redirect('pledges:index')
        token = request.POST.get('stripeToken', '')
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            charge = stripe.Charge.create(
                amount=int(float(pledge.money)) * 100,  # amount in cents, again
                currency="cad",
                card=token,
                description=request.user.username,
            )
            pledge.charge = charge.id
            pledge.is_active = True
            pledge.save()
        except stripe.CardError, _:
            messages.error(request, 'Credit Card Error')
            return redirect(reverse('pledges:detail', args=(pledge.id,)))
        return redirect(reverse('pledges:share', args=(pledge.id,)))
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
            pledge.is_active = False
            pledge.save()
        else:
            token = request.POST.get('stripeToken', '')
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                charge = stripe.Charge.create(
                    amount=int(float(pledge.money)) * 100,  # amount in cents, again
                    currency="cad",
                    card=token,
                    description=request.user.username,
                )
                pledge.charge = charge.id
                pledge.is_active = True
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
    if pledge.user != request.user.userprofile:
        return redirect(reverse('users:index'))
    if request.method == "POST":
        userprofile = UserProfile.objects.get(user=request.user)
        if userprofile.customer_id != "" and request.POST['existing'] == 'use-existing':
            customer = stripe.Customer.retrieve(userprofile.customer_id)
            if customer is None:
                messages.error(request, 'Something went wrong, please use a new credit card')
                return redirect(reverse('pledges:detail', args=(pledge.id,)))
            charge = stripe.Charge.create(
                amount=int(float(pledge.money)) * 100,  # amount in cents, again
                currency="cad",
                customer=customer,
                description=request.user.username,
            )
            pledge.charge = charge.id
            pledge.is_active = True
            pledge.save()
        else:
            token = request.POST.get('stripeToken', '')
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                stripe.Customer.create(
                    description=request.user.username,
                    card=token,
                )
                charge = stripe.Charge.create(
                    amount=int(float(pledge.money)) * 100,  # amount in cents, again
                    currency="cad",
                    card=token,
                    description=request.user.username,
                )
                pledge.charge = charge.id
                pledge.is_active = True
                pledge.save()
            except stripe.CardError, _:
                messages.error(request, 'Credit Card Error')
                return redirect(reverse('pledges:detail', args=(pledge.id,)))
        return redirect(reverse('pledges:share', args=(pledge.id,)))
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


def verify_ipn(data):
    # prepares provided data set to inform PayPal we wish to validate the response
    copy = data.copy()
    copy['cmd'] = '_notify-validate'
    params = urllib.urlencode(data)
    res = requests.post("""https://www.sandbox.paypal.com/cgi-bin/webscr""")
    # sends the data and request to the PayPal Sandbox
    response = requests.post("""https://www.sandbox.paypal.com/cgi-bin/webscr""", params)
    # reads the response back from PayPal
    status = response.text

    # If not verified
    if not status == "VERIFIED":
        return False

    # otherwise...
    return True


@csrf_exempt
def get_paypal(request):
    params = request.POST['custom'].split(',')
    course_id = params[0]
    money = params[1]
    aim = params[2]
    date = params[3]
    user_id = params[4]
    if request.POST['payment_status'] == 'Completed':
        if Pledge.objects.filter(charge=request.POST['txn_id']).count() == 0:
            course = Course.objects.get(pk=course_id)
            pledge = Pledge.objects.create(user=UserProfile.objects.get(pk=user_id), pledge_end_date=date,
                                           course=course,
                                           money=money, is_active=True, charge=request.POST['txn_id'],
                                           aim=int(aim)/100)
            action.send(request.user.userprofile, verb="pledged for", action_object=pledge, target=course)
            msg = EmailMessage('Paypal', 'created pledge', 'contact@projectwisely.com', ['tejasmehta0@gmail.com'])
            msg.send()
            return HttpResponse(json.dumps({'fail': 0, 'id': pledge.id}),
                                content_type='application/json')
    return HttpResponse()


@login_required
@csrf_exempt
def create_ajax(request):
    if request.method == "POST":
        token = request.POST.get('stripeToken', '')
        money = int(float(request.POST['money'].replace(',', '')))
        if money < 10:
            return HttpResponse(json.dumps({'fail': 1, 'message': "Can't pledge less than $10."}),
                                content_type='application/json')
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            charge = stripe.Charge.create(
                amount=money * 100,  # amount in cents, again
                currency="cad",
                card=token,
                description=request.user.username,
            )
            course = Course.objects.get(pk=int(request.POST['course']))
            date = request.POST.get('date', course.end_date)
            pledge = Pledge.objects.create(user=request.user.userprofile, pledge_end_date=date,
                                           course=course,
                                           money=money, is_active=True,
                                           aim=float(request.POST['aim'].replace('%', '')) / 100)
            action.send(request.user.userprofile, verb="pledged for", action_object=pledge, target=course)
            pledge.charge = charge.id
            pledge.is_active = True
            pledge.save()
            return HttpResponse(json.dumps({'fail': 0, 'id': pledge.id}),
                                content_type='application/json')
        except stripe.CardError, _:
            return HttpResponse(json.dumps({'fail': 1, 'message': 'Credit Card Error'}),
                                content_type='application/json')
    return HttpResponse(json.dumps({'fail': 1}),
                        content_type='application/json')


def list_rewards(request):
    user_profile = UserProfile.objects.get(user=request.user)
    rewards = Reward.objects.filter(user=user_profile)
    return render(request, 'rewards/list_rewards.html', {'rewards': rewards})


def collect_reward(request):
    if request.method == "POST":
        user_profile = UserProfile.objects.get(user=request.user)
        reward = get_object_or_404(Reward, user=user_profile, pk=request.POST.get('reward_id', ''))
        email = request.POST.get('email', '')
        if email == '':
            messages.error(request, 'Bad paypal email address, try again')
        else:
            response = mass_pay(email, float(reward.money))
            if str(response["ACK"]) != "Failure":
                messages.success(request, "Successfully collected your hard earned rewards")
                reward.collected = True
                reward.save()
            else:
                messages.error(request, "Failed to transfer money please try again later!")
        return redirect(reverse('pledges:collect_reward'))
    else:
        return redirect(reverse('users:profile'))


def myfunction():
    logger.debug("this is a debug message!")