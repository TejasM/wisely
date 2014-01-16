# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def login(request):
    if request.method == "POST":
        pass
    return render(request, 'users/login.html')


@login_required
def index(request):
    return render(request, 'users/index.html')