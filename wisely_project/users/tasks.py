from __future__ import absolute_import

from bs4 import BeautifulSoup
import time
import pytz
from users.models import Course, Quiz, Progress
from django.contrib.auth.models import User
import dateutil.parser
from django.utils import timezone


class CourseraScraper:
    def __init__(self, ):
        from selenium import webdriver
        from pyvirtualdisplay import Display

        self.display = Display(visible=0, size=(1024, 768))
        self.display.start()
        self.driver = webdriver.Firefox()
        self.courses = []

    def login(self, EMAIL, PASSWORD):
        try:
            self.driver.get('https://www.coursera.org/account/signin')
            email_field = self.driver.find_element_by_id("signin-email")
            password_field = self.driver.find_element_by_id("signin-password")
            email_field.send_keys(EMAIL)
            password_field.send_keys(PASSWORD)
            password_field.submit()
        except:
            pass

    def get_courses(self):
        try:
            soup = BeautifulSoup(self.driver.page_source)
            users_courses = soup.select(
                '.coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-name')
            return map(lambda x: x.contents[0].contents[0], users_courses), map(lambda x: x.contents[0].attrs['href'],
                                                                                users_courses)
        except:
            return [], []

    def get_quiz_link(self, course, link):
        self.driver.get(link)
        soup = BeautifulSoup(self.driver.page_source)
        link = soup.find('a', {'data-ab-user-convert': 'navclick_Quizzes'}, href=True)
        if link and link['href'] and link['href'] != '':
            if link['href'].startswith('/'):
                link['href'] = 'https://class.coursera.org' + link['href']
            course.quiz_link = link['href']
            self.driver.get(link['href'])
            soup = BeautifulSoup(self.driver.page_source)
            quiz_list = soup.select('div.course-item-list .course-item-list-header')
            quiz_details = soup.select('ul.course-item-list-section-list')
            for i, quiz_coursera in enumerate(quiz_list):
                Quiz.objects.create(heading=quiz_coursera.select('h3')[0].find(text=True, recursive=False), deadline=
                dateutil.parser.parse(str(
                    quiz_details[i].select('.course-quiz-item-softdeadline .course-assignment-deadline')[0].contents[
                        0].replace('\n', ''))),
                                    hard_deadline=str(
                                        dateutil.parser.parse(quiz_details[i].select(
                                            '.course-quiz-item-harddeadline .course-assignment-deadline')[0].contents[
                                            0].replace('\n', ''))),
                                    course=course)
            course.save()

    def get_course_progress(self, user, course):
        if course.quiz_link and course.quiz_link != '':
            self.driver.get(course.quiz_link)
            soup = BeautifulSoup(self.driver.page_source)
            quiz_list = soup.select('div.course-item-list .course-item-list-header')
            quiz_details = soup.select('ul.course-item-list-section-list')
            for i, quiz_coursera in enumerate(quiz_list):
                try:
                    quiz = Quiz.objects.get(heading=quiz_coursera.select('h3')[0].find(text=True, recursive=False),
                                            course=course)
                    try:
                        progress = Progress.objects.get(quiz=quiz, user=user.userprofile)
                    except Progress.DoesNotExist:
                        progress = Progress.objects.create(quiz=quiz, user=user.userprofile)
                    progress.score = quiz_details[i].select(
                        '.course-quiz-item-score td span')[0].contents[0]
                    progress.save()
                except Quiz.DoesNotExist:
                    print "Not found"
                except:
                    print "Error", quiz_details[i]
        user.userprofile.last_updated = timezone.now()
        user.userprofile.save()


def get_courses(user_id, scraper):
    user = User.objects.get(pk=user_id)
    if str(user.userprofile.coursera_username) != '':
        scraper.driver.implicitly_wait(10)
        scraper.login(str(user.userprofile.coursera_username), str(user.userprofile.coursera_password))
        time.sleep(3)
        courses, course_links = scraper.get_courses()
        for i, course in enumerate(courses):
            try:
                get_course = Course.objects.get(title=course)
                get_course.course_link = course_links[i]
                get_course.save()
                scraper.get_quiz_link(get_course, course_links[i])
                user.userprofile.courses.add(get_course)
            except Course.DoesNotExist:
                get_course = Course.objects.create(title=course, course_link=course_links[i])
                scraper.get_quiz_link(get_course, course_links[i])
                user.userprofile.courses.add(get_course)
            scraper.get_course_progress(user, get_course)