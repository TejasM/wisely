from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from polls.models import Question, Choice
from users.models import UserProfile


@login_required
def answer_question(request, question_id):
    if request.method == "POST":
        question = Question.objects.get(pk=question_id)
        choice = request.POST.get('choice', '')
        profile = UserProfile.objects.get(user=request.user)
        if choice != '':
            choice = Choice.objects.get(pk=choice)
            choice.votes += 1
            choice.save()
        else:
            custom = request.POST.get('custom', '')
            if custom == '':
                messages.error(request, 'Incorrectly answered survey')
                return redirect(request.POST.get('next', '/'))
            else:
                Choice.objects.create(choice_text=custom, question=question, custom=True, votes=1)
        profile.questions_answered.add(question)
        return redirect(request.POST.get('next', '/'))
    return redirect(reverse('users:index'))