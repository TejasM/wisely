import re

from lxml import html

from lxml.cssselect import CSSSelector
import requests

#from users.models import Course, Quiz, Progress


__author__ = 'Cheng'

client_id = '0aff2449c24e7732ebfb8b50549faef7'
client_password = '243ab55db462a3f52fafb3bd1c50d75448f5aa74'

status_url = 'https://www.udemy.com/api-1.1/status'
root_url = 'https://www.udemy.com/api-1.1/'
headers = {'X-Udemy-Client-Id': '0aff2449c24e7732ebfb8b50549faef7',
           'X-Udemy-Client-Secret': '243ab55db462a3f52fafb3bd1c50d75448f5aa74'}

login_start_url = 'https://www.udemy.com/join/login-popup/'
login_complete_url = 'https://www.udemy.com/join/login-submit/'
courses_url = 'https://www.udemy.com/home/my-courses/'


def check_udemy_api_status():
    client = requests.session()
    status_check = client.get(status_url, headers=headers).json()
    return status_check["status"] == 'OK'


def get_course(id):
    client = requests.session()
    course = client.get(root_url + 'courses/' + id + '/extended', headers=headers).json()
    return course


class Session:
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0',
               'X-Requested-With': 'XMLHttpRequest',
               'Referer': '	http://www.udemy.com/'}

    def __init__(self, email, password):
        self.session = requests.Session()
        self.email = email
        self.password = password

    def get(self, url):
        return self.session.get(url, headers=self.headers)

    def post(self, url, data):
        return self.session.post(url, data, headers=self.headers)

    def get_list_courses(self):
        page = self.get(courses_url)
        tree = html.fromstring(page.text)
        course_id_selector = CSSSelector('.my-course-box')
        course_ids = [e.get('data-courseid') for e in course_id_selector(tree)]
        return course_ids

    def get_csrf_token(self):
        response = self.get('http://udemy.com')
        tree = html.fromstring(response.text)
        return tree.xpath('//*[@id="signup-form"]/input[3]')[0].value

    def login(self):
        login_url = 'https://www.udemy.com/join/login-submit'
        csrf_token = self.get_csrf_token()
        payload = {'isSubmitted': 1, 'email': self.email, 'password': self.password, 'displayType': 'json',
                   'csrf': csrf_token}
        response = self.post(login_url, payload).json()
        if response.has_key('error'):
            return False
        return True

    def get_curriculum(self, id):
        ci = self.get(
            root_url + 'courses/' + id + '/curriculum?fields[lecture]=@min&fields[quiz]=@min,completionRatio,progressStatus').json()
        ci = filter(lambda x: x['type'] == 'quiz' or x['type'] == 'lecture', ci)
        return ci

    def get_course_progress(self, id):
        progress = self.get(root_url + 'courses/' + id + '/progress').json()
        return progress


def main():
    # print(check_udemy_api_status)
    # course = get_course('5678')
    session = Session('tejasmehta@live.com', 'gitajay12')
    session.login()
    courses = session.get_list_courses()
    for course in courses:
        course_dict = get_course(course)
        #todo: create course
        image_url = course_dict['images']['img_75x75']
        title = course_dict['title']
        description = re.sub('<[^>]*>', '', course_dict['promoAsset']['description'])
        course_url = course_dict['url']
        ci = session.get_curriculum(course)
        for c in ci:
            print c['id']
            #todo: create quiz
            pass
        progress = session.get_course_progress(course)
        overall_completion = progress['completion_ratio']
        #todo: set overall score
        progress = dict(progress['quiz_progress'].items() + progress['lectures_progress'].items())
        for quiz_id, quiz_marks in progress.iteritems():
            print quiz_id
            #todo create progress
            pass


def get_udemy_courses(profile):
    session = Session(profile.email, profile.password)
    r = session.login()
    if r:
        courses = session.get_list_courses()
        for course_id in courses:
            course_dict = get_course(course_id)
            try:
                course = Course.objects.get(course_id=course_id)
            except Course.DoesNotExist:
                image_url = course_dict['images']['img_75x75']
                title = course_dict['title']
                description = re.sub('<[^>]*>', '', course_dict['promoAsset']['description'])
                course_url = course_dict['url']
                course = Course.objects.create(course_id=course_id, title=title,
                                               course_link=course_url, description=description,
                                               quiz_link=root_url + 'courses/' + course_id + '/curriculum',
                                               image_link=image_url)
            #todo: create course

            ci = session.get_curriculum(course_id)
            for c in ci:
                try:
                    Quiz.objects.get(quizid=c['id'])
                except Quiz.DoesNotExist:
                    Quiz.objects.create(quizid=c['id'], course=course, heading=c['title'])
            progress = session.get_course_progress(course_id)
            overall_completion = progress['completion_ratio']
            #todo: set overall score
            progress = dict(progress['quiz_progress'].items() + progress['lectures_progress'].items())
            for quiz_id, quiz_marks in progress.iteritems():
                try:
                    quiz = Quiz.objects.get(quizid=quiz_id)
                    try:
                        progress = Progress.objects.get(user=profile, quiz=quiz)
                        progress.score = float(quiz_marks['completionRatio'])/100
                        progress.save()
                    except Progress.DoesNotExist:
                        Progress.objects.create(user=profile, quiz=quiz, score=float(quiz_marks['completionRatio'])/100)
                except Quiz.DoesNotExist:
                    pass
    else:
        profile.incorrect_login = True
        profile.save()


def pretty(d, indent=0):
    for key, value in d.iteritems():
        print '\t' * indent + str(key)
        if isinstance(value, dict):
            pretty(value, indent + 1)
        else:
            print '\t' * (indent + 1) + str(value)


if __name__ == '__main__':
    main()