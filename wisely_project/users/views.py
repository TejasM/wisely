# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect


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
    return render(request, 'users/index.html')