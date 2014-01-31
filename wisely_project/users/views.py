# Create your views here.
import json
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone
from models import UserProfile, Progress
from pledges.models import Pledge
from forms import UserProfileForm


def login_user(request):
    if request.method == "POST":
        login(request, authenticate(username=request.POST["email"], password=request.POST['password']))
        request.user.last_login = timezone.now()
        request.user.save()
        return redirect(reverse('users:index'))
    return render(request, 'base.html')


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')


@login_required
def profile(request):
    context_dict = {'user': request.user, 'user_profile': UserProfile.objects.get(user=request.user)}
    return render(request, 'users/profile.html', context_dict)


def signup(request):
    if request.method == "POST":
        user = User.objects.create(username=request.POST["email"], email=request.POST["email"],
                                   first_name=request.POST["first_name"],
                                   last_name=request.POST["last_name"])
        user.set_password(request.POST["password"])
        user.save()
        login(request, authenticate(username=request.POST["email"], password=request.POST['password']))
        request.user.last_login = timezone.now()
        request.user.save()
        return redirect(reverse('users:index'))
    return render(request, 'base.html')


@login_required
def index(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    if request.method == "POST":
        request.session['onboarding'] = request.user.userprofile.coursera_username == ""
        request.user.userprofile.coursera_username = request.POST['username']
        request.user.userprofile.coursera_password = request.POST['password']
        request.user.last_login = timezone.now()
        request.user.save()
        request.user.userprofile.save()
        if not request.session['onboarding']:
            return render(request, 'users/index.html', {'wait': True})
        else:
            return redirect(reverse('pledges:create'))
    if request.user.userprofile.coursera_username == "":
        return render(request, 'users/index.html', {'form': True})
    else:
        pledges = Pledge.objects.filter(user=profile)
        progresses = Progress.objects.filter(user=request.user.userprofile)
        return render(request, 'users/index.html', {'pledges': pledges, 'progresses': progresses, 'form': False})


def check_updated(request):
    return HttpResponse(json.dumps({'updated': request.user.last_login <= request.user.userprofile.last_updated}),
                        mimetype='application/json')


@login_required()
def edit_profile(request):
    if request.method == 'POST':
        user_profile = UserProfile.objects.get(user=request.user)

        user_profile_updated = UserProfileForm(request.POST, instance=user_profile)
        if user_profile_updated.is_valid():

            if 'picture' in request.FILES:
                user_profile.picture = request.FILES['picture']

            user_profile_updated.save()

        return HttpResponseRedirect(reverse('users:profile'))

    user_profile_form = UserProfileForm()

    return render(request, 'users/edit_profile.html', {'user_profile_form': user_profile_form})


