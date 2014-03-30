from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from studyroom.forms import CreateSessionForm
from studyroom.models import Session


def create_session(request):
    if request.method == "POST":
        form = CreateSessionForm(request.POST)
        if Session.objects.filter(name=request.POST['name'], live=True).count() == 0:
            if form.is_valid():
                session = form.save()
                return redirect(reverse('studyroom:gotosession', args=(session.id,)))
            else:
                return render(request, 'studyroom/create.html', {form: form})
        else:
            messages.error(request, "Already a session with same name is running.")
            return render(request, 'studyroom/create.html', {form: form})
    else:
        form = CreateSessionForm()
    return render(request, 'studyroom/create.html', {form: form})


def go_to_session(request, session_id):
    return None