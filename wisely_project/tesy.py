from __future__ import absolute_import

from bs4 import BeautifulSoup
import time
import pytz
import dateutil.parser


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
                '#coursera-feed-tabs-current .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-name')
            return map(lambda x: x.contents[0].contents[0], users_courses), map(lambda x: x.contents[0].attrs['href'],
                                                                                users_courses)
        except:
            return [], []

    def get_quiz_link(self, link):
        self.driver.get(link)
        soup = BeautifulSoup(self.driver.page_source)
        link = soup.find('a', {'data-ab-user-convert': 'navclick_Quizzes'}, href=True)
        if not link:
            link = soup.find('a', {'data-ab-user-convert': 'navclick_Homework_Quizzes'}, href=True)
        if not link:
            link = soup.find('a', {'data-ab-user-convert': 'navclick_Data_Sets_/_Quizzes'}, href=True)
        if not link:
            link = soup.find('a', {'data-ab-user-convert': 'navclick_Review_Questions'}, href=True)
        if not link:
            link = soup.find('a', {'data-ab-user-convert': 'navclick_Homework'}, href=True)
        if link and link['href'] and link['href'] != '':
            if link['href'].startswith('/'):
                link['href'] = 'https://class.coursera.org' + link['href']
            print link['href']
            self.driver.get(link['href'])
            soup = BeautifulSoup(self.driver.page_source)
            quiz_list = soup.select('div.course-item-list .course-item-list-header')
            quiz_details = soup.select('ul.course-item-list-section-list')
            for i, quiz_coursera in enumerate(quiz_list):
                print quiz_coursera.select('h3')[0].find(text=True, recursive=False)
                soft_deadline = None
                try:
                    print dateutil.parser.parse(str(
                        quiz_details[i].select('.course-quiz-item-softdeadline .course-assignment-deadline')[
                            0].contents[
                            0].replace('\n', '')))
                except IndexError as e:
                    print "No soft date"

                try:
                    print str(dateutil.parser.parse(quiz_details[i].select(
                        '.course-quiz-item-harddeadline .course-assignment-deadline')[0].contents[
                        0].replace('\n', '')))
                except IndexError as e:
                    print "No soft date"
        return link['href']

    def get_course_progress(self, quiz_link):
        self.driver.get(quiz_link)
        soup = BeautifulSoup(self.driver.page_source)
        quiz_list = soup.select('div.course-item-list .course-item-list-header')
        quiz_details = soup.select('ul.course-item-list-section-list')
        for i, quiz_coursera in enumerate(quiz_list):
            print quiz_coursera.select('h3')[0].find(text=True, recursive=False), quiz_details[i].select(
                '.course-quiz-item-score td span')[0].contents[0]

    def end(self):
        self.driver.close()
        self.display.stop()


def get_courses():
    scraper = CourseraScraper()
    scraper.driver.implicitly_wait(10)
    scraper.login('tejasmehta0@gmail.com', 'gitajay')
    time.sleep(3)
    courses, course_links = scraper.get_courses()
    print courses
    for i, course in enumerate(courses):
        time.sleep(3)
        print course, course_links[i]
        quiz_link = scraper.get_quiz_link(course_links[i])
        scraper.get_course_progress(quiz_link)
    scraper.end()

get_courses()


