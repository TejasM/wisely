import json
from datetime import timedelta

from actstream.models import Action
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models import Q, Avg, Sum
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string, get_template
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django_messages.models import Message
import facebook
from facebook import GraphAPIError
from notifications import notify
from requests import request as request2, HTTPError
from django.template import RequestContext
from social_auth.db.django_models import UserSocialAuth
import twitter
from actstream import action
from django.conf import settings

from models import CourseraProfile, Progress, UserProfile, EdxProfile, Invitees, UdemyProfile, Post, Course, Comments, \
    Quiz
from pledges.models import Pledge, Reward, PledgeQuiz
from forms import UserProfileForm, UserForm
from users.models import convert_to_percentage
from users.utils import send_welcome_email


def login_user(request):
    if request.method == "POST":
        user = authenticate(username=request.POST["email"], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                request.user.last_login = timezone.now()
                request.user.save()
            else:
                return redirect(reverse('users:index'))
        else:
            return redirect(reverse('users:index'))
        return redirect(reverse('users:index'))
    return redirect(reverse('users:index'))


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')


def get_suggested_followers(user):
    return UserProfile.objects.filter(~Q(pk=user.id)).filter(
        ~Q(id__in=user.follows.all().values_list('id', flat=True))).order_by('?')[:3]


@login_required
def news(request):
    if request.method == "POST":
        user_profile = UserProfile.objects.get(user=request.user)
        if request.POST['type'] == 'new':
            question = request.POST['message']
            try:
                course = Course.objects.get(pk=request.POST['course-id'])
            except Course.DoesNotExist:
                course = None
            post = Post.objects.create(question=question, user=user_profile, course=course)
            action.send(user_profile, verb='posted on', action_object=post, target=course)
            t = get_template('users/new-feed.html')
            content = t.render(RequestContext(request, {'post': post}))
            return HttpResponse(json.dumps({'fail': 0, 'content': mark_safe(content)}),
                                content_type='application/json')
        if request.POST['type'] == 'comment':
            text = request.POST['message']
            try:
                post = Post.objects.get(pk=request.POST['post-id'])
            except Course.DoesNotExist:
                return HttpResponse(json.dumps({'fail': 1}),
                                    content_type='application/json')
            Comments.objects.create(comment=text, user=user_profile, post=post)
            return HttpResponse(json.dumps(
                {'fail': 0, 'comment': text, 'user': request.user.first_name + ' ' + request.user.last_name,
                 'id': request.user.id}),
                                content_type='application/json')
        return HttpResponse(json.dumps({'fail': 1}),
                            content_type='application/json')
    else:
        feed_list = Action.objects.order_by('-timestamp')[:20]
        message_list = Message.objects.inbox_for(request.user)
        user_profile = UserProfile.objects.get(user=request.user)
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
        except UdemyProfile.DoesNotExist:
            udemy_profile = UdemyProfile.objects.create(user=request.user)

        coursera_courses = list(coursera_profile.courses.all())
        edx_courses = list(edx_profile.courses.all())
        udemy_courses = list(udemy_profile.courses.all())
        courses = coursera_courses + edx_courses + udemy_courses
        course_feeds = []
        for course in courses:
            actions = Action.objects.filter(target_object_id=course.id).order_by('-timestamp')
            course_feeds.append((list(actions), course.id))
        return render(request, 'users/news.html',
                      {'feeds': feed_list, 'message_list': message_list, 'user_profile': user_profile,
                       'all_courses': courses, 'course_feeds': course_feeds})


@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    feed_list = Action.objects.filter(actor_object_id=request.user.userprofile.id).order_by('-timestamp')[:20]

    user_profile_form = UserProfileForm(instance=user_profile)
    user_form = UserForm(instance=request.user)
    who_to_follow = get_suggested_followers(user_profile)

    pledges = Pledge.objects.filter(user=request.user.userprofile)
    message_list = Message.objects.inbox_for(request.user)
    followers = UserProfile.objects.filter(follows__in=[user_profile.id])
    user_profile = UserProfile.objects.get(user=request.user)
    rewards = Reward.objects.filter(user=user_profile)
    context_dict = {'viewed_user': request.user, 'user_profile': user_profile, 'user_profile_form': user_profile_form,
                    'user_form': user_form, 'completed_pledges': pledges, 'public': False,
                    'message_list': message_list, 'followers': followers, 'who_to_follow': who_to_follow,
                    'feeds': feed_list, 'rewards': rewards}
    return render(request, 'users/profile_alt.html', context_dict)


def public_profile(request, user_id):
    try:
        viewed_user = User.objects.get(id=user_id)
        user_profile = UserProfile.objects.get(id=viewed_user.userprofile.id)
    except (User.DoesNotExist, UserProfile.DoesNotExist) as _:
        return HttpResponseRedirect('/')

    completed_pledges = Pledge.objects.filter(user=viewed_user.userprofile, is_complete=True)
    current_pledges = Pledge.objects.filter(user=viewed_user.userprofile, is_complete=False)
    who_to_follow = get_suggested_followers(user_profile)
    feed_list = Action.objects.filter(actor_object_id=viewed_user.userprofile.id).order_by('-timestamp')[:20]

    context_dict = {'viewed_user': viewed_user, 'user_profile': user_profile, 'completed_pledges': completed_pledges,
                    'current_pledges': current_pledges, 'public': True, 'who_to_follow': who_to_follow,
                    'feeds': feed_list}
    return render(request, 'users/profile_alt.html', context_dict)


def signup(request):
    if request.method == "POST":
        if User.objects.filter(username=request.POST["email"]).count() > 0:
            messages.error(request, 'Username already taken!')
            return redirect('/')
        try:
            user = User.objects.create(username=request.POST["email"], email=request.POST["email"],
                                       first_name=request.POST["first_name"],
                                       last_name=request.POST["last_name"], is_active=True)
        except:
            messages.error(request, "Sorry username can't be longer than 30 characters")
            return redirect('/')
        user.set_password(request.POST["password"])
        user.save()
        user_profile = UserProfile.objects.create(user=user)
        action.send(user_profile, verb='joined Wisely!')
        user = authenticate(username=request.POST["email"], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                user.last_login = timezone.now()
                user.save()
                send_welcome_email(request)
            else:
                return redirect('/')
        else:
            return redirect('/')
        return redirect(reverse('users:index_alt'))
    return redirect(reverse('users:index_alt'))


def sync_up_user(user, social_users):
    try:
        inner_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist as _:
        inner_profile = UserProfile.objects.create(user=user)
    for social_user in social_users:
        if social_user.provider == 'facebook':
            if inner_profile.last_updated < timezone.now() - timedelta(weeks=2) or inner_profile.never_updated:
                graph = facebook.GraphAPI(social_user.extra_data["access_token"])
                try:
                    friends = graph.get_connections("me", "friends")
                except GraphAPIError:
                    inner_profile.last_updated = timezone.now()
                    inner_profile.never_updated = False
                    inner_profile.save()
                    return
                inner_profile.num_connections = len(friends['data'])
                for friend in friends['data']:
                    try:
                        connect = UserSocialAuth.objects.get(uid=friend["id"])
                        if connect.user not in inner_profile.connections.all():
                            inner_profile.connections.add(connect.user)
                            notify.send(sender=inner_profile, recipient=connect.user, verb='has joined Wisely')
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
        # elif social_user.provider == 'linkedin':
        #     if inner_profile.last_updated < timezone.now() - timedelta(weeks=2) or inner_profile.never_updated:
        #         try:
        #             api = linkedin.Api(consumer_key=settings.SOCIAL_AUTH_TWITTER_KEY,
        #                           consumer_secret=settings.SOCIAL_AUTH_TWITTER_SECRET,
        #                           access_token_key=social_user.extra_data['access_token']['oauth_token'],
        #                           access_token_secret=social_user.extra_data['access_token']['oauth_token_secret'])

        elif social_user.provider == 'twitter':
            if inner_profile.last_updated < timezone.now() - timedelta(weeks=2) or inner_profile.never_updated:
                try:
                    api = twitter.Api(consumer_key=settings.SOCIAL_AUTH_TWITTER_KEY,
                                      consumer_secret=settings.SOCIAL_AUTH_TWITTER_SECRET,
                                      access_token_key=social_user.extra_data['access_token']['oauth_token'],
                                      access_token_secret=social_user.extra_data['access_token']['oauth_token_secret'])
                    friends = api.GetFollowers()
                except:
                    friends = None
                inner_profile.num_connections = len(friends)
                for friend in friends:
                    try:
                        connect = UserSocialAuth.objects.get(uid=friend.id)
                        if connect.user not in inner_profile.connections.all():
                            inner_profile.connections.add(connect.user)
                            notify.send(sender=inner_profile, recipient=connect.user, verb='has joined Wisely',
                                        target=connect.user)
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
def index_alt(request):
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
    try:
        udemy_profile = UdemyProfile.objects.get(user=request.user)
    except UdemyProfile.DoesNotExist:
        udemy_profile = UdemyProfile.objects.create(user=request.user)

    if request.method == "POST":
        if request.POST['platform'] == "coursera":
            already_exist = CourseraProfile.objects.filter(~Q(user=request.user)).filter(
                username=request.POST['username'].strip()).count() > 0
            if already_exist:
                messages.success(request, 'Someone else is already using that Coursera account')
                return redirect(reverse('users:index_alt'))
            coursera_profile.username = request.POST['username'].strip()
            coursera_profile.password = request.POST['password']
            coursera_profile.incorrect_login = False
            coursera_profile.save()
            request.user.last_login = timezone.now()
            request.user.save()
            if not request.session.get('onboarding', False):
                messages.success(request, 'Added your Coursera account refresh in a few minutes to see your courses')
            return redirect(reverse('users:index_alt'))
        elif request.POST['platform'] == "edx":
            already_exist = EdxProfile.objects.filter(~Q(user=request.user)).filter(
                email=request.POST['username'].strip()).count() > 0
            if already_exist:
                messages.success(request, 'Someone else is already using that edX account')
                return redirect(reverse('users:index_alt'))

            edx_profile.email = request.POST['username'].strip()
            edx_profile.password = request.POST['password']
            edx_profile.incorrect_login = False
            edx_profile.save()
            request.user.last_login = timezone.now()
            request.user.save()
            if not request.session.get('onboarding', False):
                messages.success(request, 'Added your Edx account refresh in a few minutes to see your courses')
            return redirect(reverse('users:index_alt'))
        elif request.POST['platform'] == "udemy":
            already_exist = UdemyProfile.objects.filter(~Q(user=request.user)).filter(
                email=request.POST['username'].strip()).count() > 0
            if already_exist:
                messages.success(request, 'Someone else is already using that Udemy account')
                return redirect(reverse('users:index_alt'))
            udemy_profile.email = request.POST['username'].strip()
            udemy_profile.password = request.POST['password']
            udemy_profile.incorrect_login = False
            udemy_profile.save()
            request.user.last_login = timezone.now()
            request.user.save()
            if not request.session.get('onboarding', False):
                messages.success(request, 'Added your Udemy account refresh in a few minutes to see your courses')
            return redirect(reverse('users:index_alt'))
        else:
            messages.error(request, "Something really went wrong, please try again or contact us")
            return redirect(reverse('user:index_alt'))

    if (coursera_profile.username == "") and (
                edx_profile.email == "") and (
                udemy_profile.email == ""):
        request.session['onboarding'] = True
        request.session.save()
        return render(request, 'users/onboarding.html')
    else:
        pledges = Pledge.objects.filter(user=request.user.userprofile)
        progresses = Progress.objects.filter(user=request.user.userprofile).order_by('quiz__deadline')
        current_courses = 0
        past_courses = 0
        coursera_courses = list(coursera_profile.courses.all())
        edx_courses = list(edx_profile.courses.all())
        udemy_courses = list(udemy_profile.courses.all())

        coursera_grades = []
        edx_grades = []
        udemy_grades = []

        for course in coursera_courses:
            if course.get_amount_progress() >= 100:
                past_courses += 1
            else:
                current_courses += 1
            grades = Progress.objects.filter(quiz__course=course, user=user_profile).values_list('score', flat=True)
            if grades:
                grades = [convert_to_percentage(x) for x in grades]
                coursera_grades.append(sum(grades) / len(grades))
            else:
                coursera_grades.append(0)

        for course in edx_courses:
            if course.get_amount_progress() >= 100:
                past_courses += 1
            else:
                current_courses += 1
            grades = Progress.objects.filter(quiz__course=course, user=user_profile).values_list('score', flat=True)
            if grades:
                grades = [convert_to_percentage(x) for x in grades]
                edx_grades.append(sum(grades) / len(grades))
            else:
                edx_grades.append(0)

        for course in udemy_courses:
            if course.get_amount_progress() >= 100:
                past_courses += 1
            else:
                current_courses += 1
            grades = Progress.objects.filter(quiz__course=course, user=user_profile).values_list('score', flat=True)
            if grades:
                grades = [convert_to_percentage(x) for x in grades]
                udemy_grades.append(sum(grades) / len(grades))
            else:
                udemy_grades.append(0)

        onboarding = request.session.get('onboarding', False)
        request.session['onboarding'] = False
        request.session.save()
        return render(request, 'users/index-alt.html',
                      {'coursera_courses': zip(coursera_courses, coursera_grades),
                       'edx_courses': zip(edx_courses, edx_grades),
                       'udemy_courses': zip(udemy_courses, udemy_grades),
                       'pledges': pledges, 'progresses': progresses, 'form': False,
                       'current_courses': current_courses,
                       'past_courses': past_courses, 'onboarding': onboarding})


def to_date(date):
    if date:
        return str(date.date())
    return date


@csrf_exempt
@login_required
def get_course_stats(request):
    if request.method == "GET":
        course_id = request.GET['id']
        pledges = Pledge.objects.filter(course__id=course_id)
        avg_pledges = 'N/A'
        if pledges:
            avg_pledges = pledges.aggregate(Avg('aim')).values()[0] * 100
        count = pledges.count()
        probable_reward = 5
        if pledges:
            total_pool = pledges.aggregate(Sum('money')).values()[0]
            probable_pool = 0.2 * float(total_pool)
            probable_num_rewarded = count * 0.8
            probable_reward = probable_pool / probable_num_rewarded
        not_quizzes = PledgeQuiz.objects.filter(progress__quiz__course__id=course_id,
                                                user=request.user.userprofile).values_list(
            'progress__quiz__heading', 'progress__id', 'progress__quiz__hard_deadline', 'progress__quiz__deadline')
        today = timezone.now().date()
        quizzes = Progress.objects.filter(quiz__course__id=course_id, user=request.user.userprofile).filter(
            (Q(quiz__hard_deadline__gte=today) | Q(quiz__hard_deadline=None)) & (
                Q(quiz__deadline__gte=today) | Q(quiz__deadline=None))).values_list(
            'quiz__heading', 'id', 'score', 'quiz__hard_deadline', 'quiz__deadline')
        quizzes = [(q[0], q[1], to_date(q[3]), to_date(q[4])) for q in quizzes if convert_to_percentage(q[2]) == 0]
        quizzes = [q for q in quizzes if q not in not_quizzes]
        return HttpResponse(
            json.dumps({'fail': 0, 'avg_aim': avg_pledges, 'count': count, 'probable_reward': probable_reward,
                        'quizzes': quizzes}),
            content_type='application/json')
    return HttpResponse(json.dumps({'fail': 1}),
                        content_type='application/json')


@login_required
def check_updated(request):
    return HttpResponse(json.dumps({'updated': request.user.last_login <= request.user.courseraprofile.last_updated,
                                    'incorrect': request.user.courseraprofile.incorrect_login}),
                        content_type='application/json')


@login_required
@csrf_exempt
def force_updated(request):
    userprofile = request.user.userprofile
    userprofile.last_forced = timezone.now()
    userprofile.save()
    user = request.user
    user.last_login = timezone.now()
    user.save()
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

        context_dict = {'viewed_user': user, 'user_profile': user_profile,
                        'user_profile_form': user_profile_form,
                        'user_form': user_form,
                        'public': False,
        }

        parsed_html = render_to_string('users/_profile-alt.html',
                                       context_dict, context)

        return HttpResponse(json.dumps({'parsed_html': parsed_html, 'has_error': has_error}),
                            content_type='application/json')

    return HttpResponseRedirect(reverse('users:profile'))


@login_required
def compose(request):
    if request.method == "POST":
        sender = request.user
        recipient = request.POST['recipient']
        subject = request.POST['subject']
        body = request.POST['body']
        Message.objects.create(subject=subject, body=body, recipient=User.objects.get(username=recipient),
                               sender=User.objects.get(username=sender))
        messages.info(request, "Message successfully sent.")
        if 'successful_url' in request.POST:
            success_url = request.POST['successful_url']
        else:
            success_url = reverse('users:profile')
        return HttpResponseRedirect(success_url)
    else:
        return HttpResponseRedirect(reverse('users:profile'))


@login_required
def reply(request):
    if request.method == "POST":
        sender = request.user
        subject = request.POST['subject']
        body = request.POST['body']
        parent_msg = Message.objects.get(pk=int(request.POST['message_id']))
        recipient = parent_msg.sender
        Message.objects.create(subject=subject, body=body, recipient=recipient,
                               sender=User.objects.get(username=sender), parent_msg=parent_msg)
        messages.info(request, "Message successfully sent.")
        if 'successful_url' in request.POST:
            success_url = request.POST['successful_url']
        else:
            success_url = reverse('users:profile')
        return HttpResponseRedirect(success_url)
    else:
        return HttpResponseRedirect(reverse('users:profile'))


@csrf_exempt
@login_required
def follow(request):
    if request.method == "POST" and request.is_ajax():
        to_follow = get_object_or_404(UserProfile, pk=request.POST['user_id'])
        current_profile = request.user.userprofile
        current_profile.follows.add(to_follow)
        current_profile.save()
        notify.send(sender=request.user, recipient=to_follow.user, verb='is now following you')
        json_data = json.dumps({"HTTPRESPONSE": 1})
    else:
        json_data = json.dumps({"HTTPRESPONSE": -1})
    return HttpResponse(json_data, mimetype="application/json")


@csrf_exempt
def contact_us(request):
    if request.method == "POST":
        msg = EmailMessage(request.POST['name'], request.POST['message'], 'contact@projectwisely.com',
                           ['tejasmehta0@gmail.com'])
        msg.send()
    return HttpResponse({}, mimetype="application/json")
