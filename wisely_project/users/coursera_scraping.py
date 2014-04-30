from datetime import date, timedelta
import re
from time import timezone
import traceback

from bs4 import BeautifulSoup
import dateutil.parser


__author__ = 'tmehta'
import json
import requests
from six import print_
from pledges.models import Pledge

from users.models import Course, Quiz, Progress
from actstream import action


class CourseraDownloader(object):
    """
    Class to download content (videos, lecture notes, ...) from coursera.org for
    use offline.

    https://github.com/dgorissen/coursera-dl

    :param username: username
    :param password: password
    :keyword proxy: http proxy, eg: foo.bar.com:1234
    :keyword parser: xml parser
    :keyword ignorefiles: comma separated list of file extensions to skip (e.g., "ppt,srt")
    """
    LIST_PAGE = 'https://www.coursera.org/'
    BASE_URL = 'https://class.coursera.org/%s'
    HOME_URL = BASE_URL + '/class/index'
    LECTURE_URL = BASE_URL + '/lecture/index'
    QUIZ_URL = BASE_URL + '/quiz'
    AUTH_URL = BASE_URL + "/auth/auth_redirector?type=login&subtype=normal"
    LOGIN_URL = "https://accounts.coursera.org/api/v1/login"
    ABOUT_URL = "https://www.coursera.org/maestro/api/topic/information?topic-id=%s"

    # see
    # http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    DEFAULT_PARSER = "html.parser"

    # how long to try to open a URL before timing out
    TIMEOUT = 30.0

    def __init__(self, username,
                 password,
                 proxy=None,
                 parser=DEFAULT_PARSER,
                 ignorefiles=None,
                 max_path_part_len=None,
                 gzip_courses=False,
                 wk_filter=None):

        self.username = username
        self.password = password
        self.parser = parser

        # Split "ignorefiles" argument on commas, strip, remove prefixing dot
        # if there is one, and filter out empty tokens.
        self.session = None
        self.proxy = proxy

        try:
            self.wk_filter = map(
                int, wk_filter.split(",")) if wk_filter else None
        except Exception as e:
            print_("Invalid week filter, should be a comma separated list of integers", e)
            exit()

    def login(self, className, user):
        """
        Login into coursera and obtain the necessary session cookies.
        """
        s = requests.Session()
        if self.proxy:
            s.proxies = {'http': self.proxy}

        url = self.lecture_url_from_name(className)
        res = s.get(url, timeout=self.TIMEOUT)
        if res.status_code == 404:
            raise Exception("Unknown class %s" % className)
        res.close()

        # get the csrf token
        if 'csrf_token' not in s.cookies:
            raise Exception("Failed to find csrf cookie")

        # call the authenticator url
        LOGIN_FORM = {'email': self.username, 'password': self.password}
        s.headers['Referer'] = 'https://www.coursera.org'
        s.headers['X-CSRFToken'] = s.cookies.get('csrf_token')
        s.cookies['csrftoken'] = s.cookies.get('csrf_token')

        res = s.post(self.LOGIN_URL, data=LOGIN_FORM, timeout=self.TIMEOUT)
        if res.status_code == 401:
            raise Exception("Invalid username or password")
        res.close()

        # check if we managed to login
        if 'CAUTH' not in s.cookies:
            raise Exception("Failed to authenticate as %s" % self.username)

        self.session = s

    def get_enrollments(self, user):
        if self.session:
            url = 'https://www.coursera.org/maestro/api/topic/list2_combined'
            res = self.session.get(url)
            if res.status_code == 401:
                print "Err"
            else:
                data = json.loads(res.text)
                enrollments = data['enrollments']
                enrollments = sorted(enrollments, key=lambda x: int(x['course__topic_id']))
                topics = data['list2']['topics']
                courses = data['list2']['courses']
                if user:
                    for i, enrollment in enumerate(enrollments):
                        topic_id = enrollment['course__topic_id']
                        course_id = enrollment['course_id']
                        topic = topics[unicode(topic_id)]
                        name = topic['name']
                        course_link = None
                        quiz_link = None
                        try:
                            try:
                                course = Course.objects.get(course_id=enrollment['course__topic_id'])
                            except Course.MultipleObjectsReturned:
                                course = Course.objects.get(course_id=enrollment['course__topic_id'])[0]
                            course_id = enrollment['course_id']
                            for coursera_course in courses:
                                if coursera_course['id'] == course_id:
                                    course_link = coursera_course['home_link']
                                    quiz_link = coursera_course['home_link'] + "quiz"
                                    try:
                                        start_date = date(coursera_course['start_year'], coursera_course['start_month'],
                                                          coursera_course['start_day'])
                                    except:
                                        start_date = None
                                    end_date = None
                                    if start_date is not None and "weeks" in coursera_course['duration_string']:
                                        delta = timedelta(weeks=int(re.findall(r'\d+',
                                                                               coursera_course['duration_string'])[0]))
                                        end_date = start_date + delta
                                    if course.start_date != start_date:
                                        course.start_date = start_date
                                    if course.end_date != end_date:
                                        course.end_date = end_date
                                    course.save()
                            if course not in user.courses.all():
                                user.courses.add(course)
                                #todo: added feed check
                                #action.send(actor=user.user.userprofile, verb='enrolled in', target=course, sender=None)
                            try:
                                pledge = Pledge.objects.get(course=course, user=user)
                                if enrollment['grade_normal'] != 'null':
                                    pledge.actual_mark = int(enrollment['grade_normal'])

                            except Pledge.DoesNotExist:
                                pass
                        except Course.DoesNotExist:

                            image_link = topic['small_icon']
                            description = topic['short_description']
                            start_date = None
                            end_date = None
                            for coursera_course in courses:
                                if coursera_course['id'] == course_id:
                                    course_link = coursera_course['home_link']
                                    quiz_link = coursera_course['home_link'] + "quiz"
                                    try:
                                        start_date = date(coursera_course['start_year'], coursera_course['start_month'],
                                                      coursera_course['start_day'])
                                    except:
                                        start_date = None
                                    if start_date is not None and "weeks" in coursera_course['duration_string']:
                                        delta = timedelta(weeks=int(re.findall(r'\d+',
                                                                               coursera_course['duration_string'])[0]))
                                        end_date = start_date + delta
                            course = Course.objects.create(title=name, course_link=course_link, quiz_link=quiz_link,
                                                           start_date=start_date, end_date=end_date, image_link=image_link,
                                                           description=description, course_id=topic_id)
                            user.courses.add(course)
                            #todo: added feed check
                            #action.send(actor=user.user.userprofile, verb='enrolled in', target=course, sender=None)
                        res = self.session.get(quiz_link)
                        soup = BeautifulSoup(res.text)
                        quiz_list = soup.select('div.course-item-list .course-item-list-header')
                        quiz_details = soup.select('ul.course-item-list-section-list')
                        for j, quiz_coursera in enumerate(quiz_list):
                            heading = quiz_coursera.select('h3')[0].find(text=True, recursive=False)
                            try:
                                quiz = Quiz.objects.get(heading=heading, course=course)
                            except Quiz.MultipleObjectsReturned:
                                quiz = Quiz.objects.filter(heading=heading, course=course)[0]
                            except Quiz.DoesNotExist:
                                deadline = None
                                try:
                                    deadline = dateutil.parser.parse(str(
                                        quiz_details[j].select('.course-quiz-item-softdeadline .course-assignment-deadline')[
                                            0].contents[
                                            0].replace('\n', '')))
                                except IndexError:
                                    pass
                                hard_deadline = None
                                try:
                                    hard_deadline = dateutil.parser.parse(quiz_details[j].select(
                                        '.course-quiz-item-harddeadline .course-assignment-deadline')[0].contents[
                                                                              0].replace('\n', ''))
                                except IndexError:
                                    pass
                                if hard_deadline is None:
                                    hard_deadline = timezone.now()

                                if deadline is None:
                                    deadline = hard_deadline
                                quiz = Quiz.objects.create(heading=heading,
                                                    deadline=deadline,
                                                    hard_deadline=hard_deadline,
                                                    course=course)

                            try:
                                progress = Progress.objects.get(quiz=quiz, user=user.user.userprofile)
                            except Progress.MultipleObjectsReturned:
                                progress = Progress.objects.filter(quiz=quiz, user=user.user.userprofile)[0]
                            except Progress.DoesNotExist:
                                progress = Progress.objects.create(quiz=quiz, user=user.user.userprofile)
                            progress.score = quiz_details[j].select(
                                '.course-quiz-item-score td span')[0].contents[0]
                            progress.save()
                    user.save()
                else:
                    for i, enrollment in enumerate(enrollments):
                        topic_id = enrollment['course__topic_id']
                        course_id = enrollment['course_id']
                        topic = topics[unicode(topic_id)]
                        name = topic['name']
                        course_link = None
                        quiz_link = None
                        image_link = topic['small_icon']
                        description = topic['short_description']
                        start_date = None
                        end_date = None
                        for coursera_course in courses:
                            if coursera_course['id'] == course_id:
                                course_link = coursera_course['home_link']
                                quiz_link = coursera_course['home_link'] + "quiz"
                                start_date = date(coursera_course['start_year'], coursera_course['start_month'],
                                                  coursera_course['start_day'])
                                if "weeks" in coursera_course['duration_string']:
                                    delta = timedelta(weeks=int(re.findall(r'\d+',
                                                                           coursera_course['duration_string'])[0]))
                                    end_date = start_date + delta

                        print name
                        print course_link
                        print quiz_link
                        print start_date
                        print end_date
                        print image_link
                        print description
                        res.close()
                        res = self.session.get(quiz_link)
                        soup = BeautifulSoup(res.text)
                        quiz_list = soup.select('div.course-item-list .course-item-list-header')
                        quiz_details = soup.select('ul.course-item-list-section-list')
                        for i, quiz_coursera in enumerate(quiz_list):
                            print quiz_coursera.select('h3')[0].find(text=True, recursive=False)
            res.close()

    def course_name_from_url(self, course_url):
        """Given the course URL, return the name, e.g., algo2012-p2"""
        return course_url.split('/')[3]

    def lecture_url_from_name(self, course_name):
        """Given the name of a course, return the video lecture url"""
        return self.LECTURE_URL % course_name

    # TODO: simple hack, something more elaborate needed
    def trim_path_part(self, s):
        mppl = self.max_path_part_len
        if mppl and len(s) > mppl:
            return s[:mppl]
        else:
            return s

    def get_response(self, url, retries=3, **kwargs):
        """
        Get the response
        """
        kwargs.update(timeout=self.TIMEOUT, allow_redirects=True)
        for i in range(retries):
            try:
                r = self.session.get(url, **kwargs)
                r.raise_for_status()
            except Exception as e:
                # print_("Warning: Retrying to connect url:%s" % url)
                pass
            else:
                return r
        raise e

    def get_headers(self, url):
        """
        Get the headers
        """
        r = self.get_response(url, stream=True)
        headers = r.headers
        r.close()
        return headers

    def get_page(self, url):
        """
        Get the content
        """
        r = self.get_response(url)
        page = r.content
        r.close()
        return page

    def get_json(self, url):
        """
        Get the json data
        """
        r = self.get_response(url)
        data = r.json()
        r.close()
        return data

    def get_json_get(self, url, get_data):
        """
        Get the json data
        """
        r = self.session.get(url, data=get_data)
        data = r.json()
        r.close()
        return data


def main():
    coursera = CourseraDownloader('tejasmehta0@gmail.com', 'gitajay')
    coursera.login('gamification-003', None)
    coursera.get_enrollments(None)

if __name__ == '__main__':
    main()