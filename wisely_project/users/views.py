import json
from datetime import timedelta
import urllib

from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
import facebook
import oauth2
from requests import request as request2, HTTPError
from django.template import RequestContext
from social_auth.db.django_models import UserSocialAuth
import twitter

from models import CourseraProfile, Progress, UserProfile, EdxProfile, Invitees
from pledges.models import Pledge
from forms import UserProfileForm, UserForm
from users.utils import send_welcome_email
from wisely_project.settings import base


def login_user(request):
    if request.method == "POST":
        user = authenticate(username=request.POST["email"], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                request.user.last_login = timezone.now()
                request.user.save()
            else:
                return render(request, 'base.html')
        else:
            return render(request, 'base.html')
        return redirect(reverse('users:index'))
    return redirect('/')


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    user_profile_form = UserProfileForm(instance=user_profile)
    user_form = UserForm(instance=request.user)

    completed_pledges = Pledge.objects.filter(user=request.user.userprofile, is_complete=True)
    current_pledges = Pledge.objects.filter(user=request.user.userprofile, is_complete=False)

    context_dict = {'user': request.user, 'user_profile': user_profile, 'user_profile_form': user_profile_form,
                    'user_form': user_form, 'completed_pledges': completed_pledges, 'current_pledges': current_pledges}
    return render(request, 'users/profile.html', context_dict)


def public_profile(request, user_id):
    try:
        viewed_user = User.objects.get(id=user_id)
        user_profile = UserProfile.objects.get(user=viewed_user)
    except (User.DoesNotExist, UserProfile.DoesNotExist) as _:
        return HttpResponseRedirect('/')

    completed_pledges = Pledge.objects.filter(user=viewed_user.userprofile, is_complete=True)
    current_pledges = Pledge.objects.filter(user=viewed_user.userprofile, is_complete=False)

    context_dict = {'viewed_user': viewed_user, 'user_profile': user_profile, 'completed_pledges': completed_pledges,
                    'current_pledges': current_pledges, 'public': True}
    return render(request, 'users/profile.html', context_dict)


def signup(request):
    if request.method == "POST":
        if User.objects.filter(username=request.POST["email"]).count() > 0:
            messages.error(request, 'Username already taken!')
            return redirect('/')
        user = User.objects.create(username=request.POST["email"], email=request.POST["email"],
                                   first_name=request.POST["first_name"],
                                   last_name=request.POST["last_name"], is_active=True)
        user.set_password(request.POST["password"])
        user.save()
        UserProfile.objects.create(user=user)
        user = authenticate(username=request.POST["email"], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                user.last_login = timezone.now()
                user.save()
                send_welcome_email(request)
            else:
                return render(request, 'base.html')
        else:
            return render(request, 'base.html')
        return redirect(reverse('users:index'))
    return render(request, 'base.html')


def sync_up_user(user, social_users):
    try:
        inner_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist as _:
        inner_profile = UserProfile.objects.create(user=user)
    for social_user in social_users:
        if social_user.provider == 'facebook':
            if inner_profile.last_updated < timezone.now() - timedelta(weeks=2) or inner_profile.never_updated:
                graph = facebook.GraphAPI(social_user.extra_data["access_token"])
                friends = graph.get_connections("me", "friends")
                inner_profile.num_connections = len(friends['data'])
                for friend in friends['data']:
                    try:
                        connect = UserSocialAuth.objects.get(uid=friend["id"])
                        if connect.user not in inner_profile.connections.all():
                            inner_profile.connections.add(connect.user)
                        try:
                            connect = UserProfile.objects.get(user=connect.user)
                        except UserProfile.DoesNotExist as _:
                            connect = UserProfile.objects.create(user=connect.user)
                        connect.connections.add(user)
                        connect.save()
                    except UserSocialAuth.DoesNotExist as _:
                        try:
                            Invitees.objects.get(uid=friend["id"], user_from=inner_profile)
                        except Invitees.DoesNotExist as _:
                            Invitees.objects.create(uid=friend["id"], user_from=inner_profile,
                                                    name=friend['name'], social_media='facebook')
                inner_profile.last_updated = timezone.now()
                inner_profile.never_updated = False
                inner_profile.save()

        elif social_user.provider == 'twitter':
            if inner_profile.last_updated < timezone.now() - timedelta(weeks=2) or inner_profile.never_updated:
                api = twitter.Api(consumer_key=base.TWITTER_CONSUMER_KEY,
                                  consumer_secret=base.TWITTER_CONSUMER_SECRET,
                                  access_token_key=social_user.tokens['oauth_token'],
                                  access_token_secret=social_user.tokens['oauth_token_secret'])
                friends = api.GetFollowers()
                inner_profile.num_connections = len(friends)
                for friend in friends:
                    try:
                        connect = UserSocialAuth.objects.get(uid=friend.id)
                        if connect.user not in inner_profile.connections.all():
                            inner_profile.connections.add(connect.user)
                        try:
                            connect = UserProfile.objects.get(user=connect.user)
                        except UserProfile.DoesNotExist as _:
                            connect = UserProfile.objects.create(user=connect.user)
                        connect.connections.add(user)
                        connect.save()
                    except UserSocialAuth.DoesNotExist as _:
                        try:
                            Invitees.objects.get(uid=friend.id, user_from=inner_profile)
                        except Invitees.DoesNotExist as _:
                            Invitees.objects.create(uid=friend.id, user_from=inner_profile,
                                                    name=friend.name, social_media='twitter')
                inner_profile.last_updated = timezone.now()
                inner_profile.never_updated = False
                inner_profile.save()


@login_required
def index(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    social_users = UserSocialAuth.objects.filter(user=request.user)
    sync_up_user(request.user, social_users)
    if user_profile.picture._file is None and request.user.social_auth.all().count() > 0 and \
                    request.user.social_auth.all()[0].provider == 'facebook':
        url = 'http://graph.facebook.com/{0}/picture'.format(request.user.social_auth.all()[0].uid)
        try:
            response = request2('GET', url, params={'type': 'large'})
            response.raise_for_status()
            user_profile.picture.save('{0}_social.jpg'.format(request.user.username),
                                      ContentFile(response.content))
            user_profile.save()
        except HTTPError:
            pass
    try:
        coursera_profile = CourseraProfile.objects.get(user=request.user)
    except CourseraProfile.DoesNotExist:
        coursera_profile = CourseraProfile.objects.create(user=request.user)
    try:
        edx_profile = EdxProfile.objects.get(user=request.user)
    except EdxProfile.DoesNotExist:
        edx_profile = EdxProfile.objects.create(user=request.user)

    if request.method == "POST":
        request.session['onboarding'] = coursera_profile.username == "" and edx_profile.email == ""
        request.session.save()
        if request.POST['platform'] == "coursera":
            request.user.courseraprofile.username = request.POST['username'].strip()
            already_exist = CourseraProfile.objects.filter(username=request.user.courseraprofile.username).count() > 0
            if already_exist:
                if not request.session['onboarding']:
                    messages.success(request, 'Someone else is already using that Coursera account')
                    return redirect(reverse('users:index'))
                return render(request, 'users/index.html', {'alreadyExistCoursera': True})

            request.user.courseraprofile.password = request.POST['password']
            request.user.courseraprofile.save()
            request.user.last_login = timezone.now()
            request.user.save()
            if not request.session['onboarding']:
                messages.success(request, 'Added your Coursera account refresh in a few minutes to see your courses')
                return redirect(reverse('users:index'))
            else:
                return redirect(reverse('pledges:create'))
        elif request.POST['platform'] == "edx":
            request.user.edxprofile.email = request.POST['username'].strip()
            already_exist = EdxProfile.objects.filter(email=request.user.edxprofile.email).count() > 0
            if already_exist:
                if not request.session['onboarding']:
                    messages.success(request, 'Someone else is already using that Edx account')
                    return redirect(reverse('users:index'))
                return render(request, 'users/index.html', {'alreadyExistEdx': True})

            request.user.edxprofile.password = request.POST['password']
            request.user.edxprofile.save()
            request.user.last_login = timezone.now()
            request.user.save()
            if not request.session['onboarding']:
                messages.success(request, 'Added your Edx account refresh in a few minutes to see your courses')
                return redirect(reverse('users:index'))
            else:
                return redirect(reverse('pledges:create'))
        else:
            messages.error(request, "Something really went wrong, please try again or contact us")
            return redirect(reverse('user:index'))

    if (coursera_profile.username == "" or coursera_profile.incorrect_login) and (
                    edx_profile.email == "" or edx_profile.incorrect_login):
        return render(request, 'users/index.html', {'form': True})
    else:
        pledges = Pledge.objects.filter(user=request.user.userprofile)
        progresses = Progress.objects.filter(user=request.user.userprofile)
        other_pledgers_coursera = []
        other_pledgers_edx = []
        for course in coursera_profile.courses.all():
            other_pledgers_coursera.append(Pledge.objects.filter(course=course).order_by('?')[:5])
        for course in edx_profile.courses.all():
            other_pledgers_edx.append(Pledge.objects.filter(course=course).order_by('?')[:5])
        return render(request, 'users/index.html', {'pledges': pledges, 'progresses': progresses, 'form': False,
                                                    'others_coursera': other_pledgers_coursera,
                                                    'others_edx': other_pledgers_edx})


@login_required
def check_updated(request):
    return HttpResponse(json.dumps({'updated': request.user.last_login <= request.user.courseraprofile.last_updated,
                                    'incorrect': request.user.courseraprofile.incorrect_login}),
                        content_type='application/json')


@login_required
def force_updated(request):
    userprofile = request.user.userprofile
    if userprofile.last_forced is None or (
                    userprofile.last_forced is not None and userprofile.last_forced.date() != timezone.now().date()):
        userprofile.last_forced = timezone.now()
        userprofile.save()
        user = request.user
        user.last_login = timezone.now()
        user.save()
    else:
        return HttpResponse(json.dumps({'fail': True}),
                            content_type='application/json')
    return HttpResponse(json.dumps({}),
                        content_type='application/json')


@login_required
def edit_profile(request):
    if request.method == 'POST':
        context = RequestContext(request)
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile_form = UserProfileForm(data=request.POST, instance=user_profile)
        user_form = UserForm(data=request.POST, instance=request.user)

        print request.POST
        has_error = False
        if user_profile_form.is_valid() and user_form.is_valid():
            print "is valid"

            if 'picture' in request.FILES:
                user_profile.picture = request.FILES['picture']

            user_form.save()
            user_profile_form.save()
            user = User.objects.get(id=request.user.id)
            user_profile = UserProfile.objects.get(user=user)
            user_profile_form = UserProfileForm(instance=user_profile)
            user_form = UserForm(instance=user)
        else:
            user = User.objects.get(id=request.user.id)
            has_error = True
            print user_profile_form.errors, user_form.errors

        completed_pledges = Pledge.objects.filter(user=request.user.userprofile, is_complete=True)
        current_pledges = Pledge.objects.filter(user=request.user.userprofile, is_complete=False)

        context_dict = {'user': user, 'user_profile': user_profile,
                        'user_profile_form': user_profile_form,
                        'user_form': user_form, 'completed_pledges': completed_pledges,
                        'current_pledges': current_pledges}

        parsed_html = render_to_string('users/_profile.html',
                                       context_dict, context)

        return HttpResponse(json.dumps({'parsed_html': parsed_html, 'has_error': has_error}),
                            content_type='application/json')

    return HttpResponseRedirect(reverse('users:profile'))





