# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from tasks import get_courses
from models import UserProfile


def login(request):
    if request.method == "POST":
        pass
    return render(request, 'base.html')


def signup(request):
    if request.method == "POST":
        user = User.objects.create(username=request.POST["email"], email=request.POST["email"],
                                   first_name=request.POST["first_name"],
                                   last_name=request.POST["last_name"])
        user.set_password(request.POST["password"])
        user.save()
        return redirect(reverse('user:login'))
    return render(request, 'base.html')


@login_required
def index(request):
    try:
        UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user)
    if request.method == "POST":
        request.user.userprofile.coursera_username = request.POST['username']
        request.user.userprofile.coursera_password = request.POST['password']
        request.user.userprofile.save()
        get_courses.delay(request.user)
    if request.user.userprofile.coursera_username == "":
        return render(request, 'users/index.html', {'form': True})
    else:
        get_courses.delay(request.user)
        pass
    return render(request, 'users/index.html')