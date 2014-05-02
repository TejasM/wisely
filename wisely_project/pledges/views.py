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
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import stripe

from users.models import Course, UserProfile, EdxProfile, CourseraProfile, UdemyProfile
from users.utils import divide_timedelta


__author__ = 'Cheng'

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from models import Pledge, Follower, Reward
from actstream import action
from django.conf import settings


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


logger = logging.getLogger(__name__)


def verify_ipn(data):
    # prepares provided data set to inform PayPal we wish to validate the response
    params = urllib.urlencode(data)

    # sends the data and request to the PayPal Sandbox
    req = urllib2.Request("""https://www.sandbox.paypal.com/cgi-bin/webscr""", params)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    # reads the response back from PayPal
    response = urllib2.urlopen(req)
    status = response.read()

    # If not verified
    if not status == "VERIFIED":
        return False

    # if not the correct receiver ID
    if not data["receiver_id"] == "DDBSOMETHING4KE":
        return False

    # if not the correct currency
    if not data["mc_currency"] == "USD":
        return False

    # otherwise...
    return True


@csrf_exempt
def get_paypal(request):
    logger.debug("get request")
    if verify_ipn(request.POST):
        if request.POST['payment_status'] == 'Completed':
            logger.debug("is completed")
            if Pledge.objects.filter(charge=request.POST['txn_id']).count() == 0:
                if request.POST['money'] == request.POST['mc_gross1']:
                    logger.debug("money equals")
                    money = int(float(request.POST['money'].replace(',', '')))
                    if money < 10:
                        return HttpResponse(json.dumps({'fail': 1, 'message': "Can't pledge less than $10."}),
                                            content_type='application/json')
                    course = Course.objects.get(pk=int(request.GET['course']))
                    date = request.POST.get('date', course.end_date)
                    user_profile = UserProfile.objects.get(pk=request.GET['user'])
                    pledge = Pledge.objects.create(user=user_profile, pledge_end_date=date,
                                                   course=course,
                                                   money=money, is_active=True,
                                                   aim=float(request.POST['aim'].replace('%', '')) / 100)
                    action.send(user_profile, verb="pledged for", action_object=pledge, target=course)
                    pledge.charge = request.GET['txn_id']
                    pledge.is_active = True
                    pledge.save()
                    return HttpResponse(json.dumps({'fail': 0, 'id': pledge.id}),
                                        content_type='application/json')
                return HttpResponse(json.dumps({'fail': 3}),
                                    content_type='application/json')
            return HttpResponse(json.dumps({'fail': 3}),
                                content_type='application/json')


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


@login_required
def create(request):
    if request.method == "POST":
        if request.POST.get('onboarding', '') != '':
            course = Course.objects.get(pk=int(request.POST['course']))
            pledge = Pledge.objects.create(user=request.user.userprofile,
                                           course=course,
                                           money=int(float(request.POST['money'].replace(',', ''))), is_active=False,
                                           aim=float(request.POST['aim'].replace('%', '')) / 100)
            action.send(request.user.userprofile, verb="pledged for", action_object=pledge, target=course)
            return redirect(reverse('pledges:detail', args=(pledge.id,)))
    try:
        coursera_profile = CourseraProfile.objects.get(user=request.user)
    except CourseraProfile.DoesNotExist:
        coursera_profile = CourseraProfile.objects.create(user=request.user)
    try:
        edx_profile = EdxProfile.objects.get(user=request.user)
    except EdxProfile.DoesNotExist:
        edx_profile = EdxProfile.objects.create(user=request.user)
    try:
        udemy_profile = UdemyProfile.objects.get(user=request.user)
    except EdxProfile.DoesNotExist:
        udemy_profile = UdemyProfile.objects.create(user=request.user)

    if coursera_profile.username == '' and edx_profile.email == '' and udemy_profile.email == '':
        request.session['onboarding'] = True
        request.session.save()
        return redirect(reverse('users:index'))
    other_pledgers_list = []
    projections = []
    pledged_courses = Pledge.objects.filter(user=request.user.userprofile).values_list('course_id')
    if pledged_courses:
        courses_available = request.user.courseraprofile.courses.filter(~Q(pk__in=pledged_courses))
    else:
        courses_available = request.user.courseraprofile.courses.all()
    try:
        if pledged_courses:
            courses_available = courses_available | request.user.edxprofile.courses.filter(~Q(pk__in=pledged_courses))
        else:
            courses_available = courses_available | request.user.edxprofile.courses.all()
    except EdxProfile.DoesNotExist:
        pass
    try:
        if pledged_courses:
            courses_available = courses_available | request.user.udemyprofile.courses.filter(~Q(pk__in=pledged_courses))
        else:
            courses_available = courses_available | request.user.udemyprofile.courses.all()
    except UdemyProfile.DoesNotExist:
        pass

    to_keep = []

    for course_available in courses_available:
        if course_available.start_date is None or course_available.end_date is None:
            if course_available.end_date is None:
                to_keep.append(course_available.id)
            elif course_available.end_date > timezone.now().date() + relativedelta(months=2):
                to_keep.append(course_available.id)
            continue
        total_time = course_available.end_date - course_available.start_date
        if course_available.start_date + divide_timedelta(total_time, 2) > timezone.now().date():
            to_keep.append(course_available.id)
    courses_available = courses_available.filter(pk__in=to_keep)
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