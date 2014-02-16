import json

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
from requests import request as request2, HTTPError
from django.template import RequestContext

from models import CourseraProfile, Progress, UserProfile
from pledges.models import Pledge
from forms import UserProfileForm, UserForm


def login_user(request):
    if request.method == "POST":
        user = authenticate(username=request.POST["email"], password=request.POST['password'])
        login(request, user)
        request.user.last_login = timezone.now()
        request.user.save()
        return redirect(reverse('users:index'))
    return render(request, 'base.html')


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
    except User.DoesNotExist or UserProfile.DoesNotExist:
        return HttpResponseRedirect('/')

    completed_pledges = Pledge.objects.filter(user=request.user.userprofile, is_complete=True)
    current_pledges = Pledge.objects.filter(user=request.user.userprofile, is_complete=False)

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
        else:
            return render(request, 'base.html')
        return redirect(reverse('users:index'))
    return render(request, 'base.html')


@login_required
def index(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    if user_profile.picture._file is None:
        if request.user.social_auth.all().count() > 0 and request.user.social_auth.all()[0].provider == 'facebook':
            url = 'http://graph.facebook.com/{0}/picture'.format(request.user.social_auth.all()[0].uid)
            try:
                response = request2('GET', url, params={'type': 'large'})
                response.raise_for_status()
            except HTTPError:
                pass
            user_profile.picture.save('{0}_social.jpg'.format(request.user.username),
                                      ContentFile(response.content))
            user_profile.save()
    try:
        coursera_profile = CourseraProfile.objects.get(user=request.user)
    except CourseraProfile.DoesNotExist:
        coursera_profile = CourseraProfile.objects.create(user=request.user)

    if request.method == "POST":
        request.session['onboarding'] = coursera_profile.username == ""
        request.user.courseraprofile.username = request.POST['username']
        request.user.courseraprofile.password = request.POST['password']
        request.user.courseraprofile.save()
        request.user.last_login = timezone.now()
        request.user.save()
        if not request.session['onboarding']:
            return render(request, 'users/index.html', {'wait': True})
        else:
            return redirect(reverse('pledges:create'))

    if coursera_profile.username == "" or coursera_profile.incorrect_login:
        return render(request, 'users/index.html', {'form': True})
    else:
        pledges = Pledge.objects.filter(user=request.user.userprofile)
        progresses = Progress.objects.filter(user=request.user.userprofile)
        other_pledgers_list = []
        for course in coursera_profile.courses.all():
            other_pledgers_list.append(Pledge.objects.filter(course=course).order_by('?')[:5])
        return render(request, 'users/index.html', {'pledges': pledges, 'progresses': progresses, 'form': False,
                                                    'others': other_pledgers_list})


def check_updated(request):
    return HttpResponse(json.dumps({'updated': request.user.last_login <= request.user.courseraprofile.last_updated,
                                    'incorrect': request.user.courseraprofile.incorrect_login}),
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





