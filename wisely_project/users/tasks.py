from __future__ import absolute_import

from celery import shared_task

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import sys
from wisely_project.celery import app


class CourseraScraper:
    def __init__(self, EMAIL, PASSWORD):
        self.driver = webdriver.Firefox()
        self.email = EMAIL
        self.password = PASSWORD
        self.courses = []

    def login(self):
        self.driver.get('https://www.coursera.org/account/signin')
        email_field = self.driver.find_element_by_id("signin-email")
        password_field = self.driver.find_element_by_id("signin-password")
        email_field.send_keys(self.email)
        password_field.send_keys(self.password)
        password_field.submit()

    def get_courses(self):
        soup = BeautifulSoup(self.driver.page_source)
        users_courses = soup.select(
            '.coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-name')
        return map(lambda x: x.contents[0].contents[0], users_courses), map(lambda x: x.contents[0].attrs['href'],
                                                                            users_courses)

    def get_assignments(self, link):
        self.driver.get(link)
        soup = BeautifulSoup(self.driver.page_source)
        link = soup.find('a', {'data-ab-user-convert': 'navclick_Quizzes'})
        print link


@app.task
def get_courses(user):
    scraper = CourseraScraper(user.user_profile.get.coursera_username, user.user_profile.get.coursera_password)
    scraper.driver.implicitly_wait(10)
    scraper.login()
    time.sleep(3)
    courses, course_links = scraper.get_courses()
    for link in course_links:
        scraper.get_assignments(link)
    scraper.driver.close()