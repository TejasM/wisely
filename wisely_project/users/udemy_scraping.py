import re

from lxml import html

from lxml.cssselect import CSSSelector
import requests

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
    try:
        r = client.get(root_url + 'courses/' + id, headers=headers)
        course = r.json()
    except:
        print client.get(root_url + 'courses/' + id, headers=headers)
        course = []
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
        page = self.get(root_url + 'users/me/taking').json()
        course_ids = map(lambda x: x['id'],page['courses'])
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
            root_url + 'courses/' + id + '/curriculum').json()
        ci = filter(lambda x: x['type'] == 'quiz' or x['type'] == 'lecture', ci)
        return ci

    def get_course_progress(self, id):
        progress = self.get(root_url + 'courses/' + id + '/progress').json()
        return progress


def main():
    # print(check_udemy_api_status)
    # course = get_course('5678')
    session = Session('tejasmehta@live.com', 'gitajay12')
    r = session.login()
    print r
    courses = session.get_list_courses()
    print courses
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


def pretty(d, indent=0):
    for key, value in d.iteritems():
        print '\t' * indent + str(key)
        if isinstance(value, dict):
            pretty(value, indent + 1)
        else:
            print '\t' * (indent + 1) + str(value)


if __name__ == '__main__':
    main()