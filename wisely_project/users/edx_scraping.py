from datetime import datetime
from fractions import Fraction

from django.utils import timezone
from actstream import action

from lxml.cssselect import CSSSelector
from pledges.models import Pledge
from users.models import Course, Quiz, Progress


__author__ = 'tmehta'
from lxml import html
import requests

login_url = 'https://courses.edx.org/login_ajax'

URL = 'https://courses.edx.org/login'


def scrape_for_user(edxprofile):
    try:
        email = edxprofile.email
        password = edxprofile.password
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets cookie
        csrftoken = client.cookies['csrftoken']

        login_data = dict(email=email, password=password, csrfmiddlewaretoken=csrftoken, redirect_url='/dashboard')
        r = client.post(login_url, data=login_data, headers=dict(Referer=URL))
        if 'false' in r.text:
            print "incorrect"
            edxprofile.incorrect_login = True
            edxprofile.save()
            return
        page = client.get('https://courses.edx.org/dashboard')
        tree = html.fromstring(page.text)

        course_id_selector = CSSSelector('.unenroll')
        course_ids = [e.get('data-course-number') for e in course_id_selector(tree)]

        #images:
        image_selector = CSSSelector('.course-item .cover img')
        image_links = ['https://courses.edx.org/' + e.get('src') for e in image_selector(tree)]

        #Current or Completed
        name_selector = CSSSelector('.course-item .info hgroup h3 a')
        current_courses = [e.text for e in name_selector(tree)]
        course_links = ['https://courses.edx.org/' + e.get('href') for e in name_selector(tree)]
        progress_links = ['https://courses.edx.org/' + e.get('href').replace('info', 'progress') for e in
                          name_selector(tree)]

        #Upcoming
        name_selector = CSSSelector('.course-item .info hgroup h3 span')
        upcoming_courses = [e.text for e in name_selector(tree)]

        current_courses += upcoming_courses

        #Dates
        date_selector = CSSSelector('.course-item .info hgroup p.date-block')
        dates = [e.text.replace('\n', '').strip() for e in date_selector(tree)]

        for i, current_course in enumerate(current_courses):
            course = None
            try:
                course = Course.objects.get(course_id=course_ids[i])
                if course.course_link == '':
                    course.course_link = course_links[i]
                    course.quiz_link = progress_links[i]
                if course.start_date is None and 'Course Started' in dates[i]:
                    try:
                        course.start_date = datetime.strptime(dates[i].replace('Course Started - ', ''),
                                                              '%b %d, %Y').date()
                    except:
                        pass
                if course.end_date is None and 'Course Completed' in dates[i]:
                    try:
                        course.end_date = datetime.strptime(dates[i].replace('Course Completed - ', ''),
                                                            '%b %d, %Y').date()
                    except:
                        pass
                course.save()
            except Course.DoesNotExist:
                if 'Course Completed' in dates[i]:
                    date_real = None
                    try:
                        date_real = datetime.strptime(dates[i].replace('Course Completed - ', ''),
                                                      '%b %d, %Y').date()
                    except:
                        pass
                    course = Course.objects.create(course_id=course_ids[i], title=current_course,
                                                   course_link=course_links[i], quiz_link=progress_links[i],
                                                   image_link=image_links[i],
                                                   end_date=date_real)
                elif 'Course Started' in dates[i]:
                    date_real = None
                    try:
                        date_real = datetime.strptime(dates[i].replace('Course Started - ', ''),
                                                      '%b %d, %Y').date()
                    except:
                        pass
                    course = Course.objects.create(course_id=course_ids[i], title=current_course,
                                                   course_link=course_links[i], quiz_link=progress_links[i],
                                                   image_link=image_links[i],
                                                   start_date=date_real)
            if course is not None:
                if course not in edxprofile.courses.all():
                    edxprofile.courses.add(course)
                    #todo: added feed check
                    #action.send(actor=edxprofile.user.userprofile, verb='enrolled in', target=course, sender=None)

        edxprofile.last_updated = timezone.now()
        edxprofile.save()

        info_selector = CSSSelector('.course-item .info')
        eles = [e for e in info_selector(tree)]
        inner_grade_selector = CSSSelector('.grade-value:first-child')
        for i, ele in enumerate(eles):
            final_marks = [e.text.replace('\n', '').strip() for e in inner_grade_selector(ele)]
            if final_marks:
                pledges = Pledge.objects.filter(user=edxprofile.user.userprofile, course__course_id=course_ids[i])
                if pledges.count() > 0:
                    for pledge in pledges:
                        pledge.actual_mark = final_marks
                        pledge.save()
        for i, link in enumerate(progress_links):
            r = client.get(link)
            page = html.fromstring(r.text)
            title_selector = CSSSelector('.chapters section h2')
            progress_titles = [e.text.replace('\n', '').strip() for e in title_selector(page)]
            for progress_title in progress_titles:
                try:
                    quiz = Quiz.objects.get(course__course_id=course_ids[i], heading=progress_title)
                except Quiz.DoesNotExist:
                    try:
                        c = Course.objects.get(course_id=course_ids[i])
                    except Course.DoesNotExist:
                        c = Course.objects.create(course_id=course_ids[i], title=current_courses[i])
                    quiz = Quiz.objects.create(course=c,
                                               heading=progress_title)
                section_selector = CSSSelector('.chapters section')
                sections = [e for e in section_selector(page)]
                scores_selector = CSSSelector('.scores li')
                mark = None
                for section in sections:
                    marks = [e.text.replace('\n', '').strip() for e in scores_selector(section)]
                    try:
                        if marks:
                            mark = sum(
                                map(lambda x: Fraction(x) if not x.endswith('/0') else Fraction(0),
                                    marks))
                            if mark != Fraction(0):
                                print marks
                                print str(mark.numerator) + "/" + str(mark.denominator)
                            mark = str(mark.numerator) + "/" + str(mark.denominator)
                        else:
                            mark = "0/0"
                    except:
                        mark = "0/0"
                if mark is not None:
                    try:
                        progress = Progress.objects.get(user=edxprofile.user.userprofile, quiz=quiz)
                        progress.score = mark
                        progress.save()
                    except Progress.DoesNotExist:
                        Progress.objects.create(user=edxprofile.user.userprofile, quiz=quiz, score=mark)
        print "Edx Done"
    except Exception as e:
        print e