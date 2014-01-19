from __future__ import absolute_import
import logging

from celery import shared_task

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import sys
from wisely_project.celery import app
from users.models import Course
from celery.utils.log import get_task_logger


class CourseraScraper:
    def __init__(self, EMAIL, PASSWORD):
        self.driver = webdriver.Firefox()
        self.email = EMAIL
        self.password = PASSWORD
        self.courses = []

    def login(self):
        try:
            self.driver.get('https://www.coursera.org/account/signin')
            email_field = self.driver.find_element_by_id("signin-email")
            password_field = self.driver.find_element_by_id("signin-password")
            email_field.send_keys(self.email)
            password_field.send_keys(self.password)
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

    def get_assignments(self, link):
        self.driver.get(link)
        soup = BeautifulSoup(self.driver.page_source)
        link = soup.find('a', {'data-ab-user-convert': 'navclick_Quizzes'})
        print link


@app.task
def get_courses(user):
    logger = get_task_logger(__name__)
    logger.info('started')
    scraper = CourseraScraper(str(user.userprofile.coursera_username), str(user.userprofile.coursera_password))
    scraper.driver.implicitly_wait(10)
    scraper.login()
    time.sleep(3)
    courses, course_links = scraper.get_courses()
    logger.info('got courses')
    for course in courses:
        try:
            Course.objects.get(title=course)
        except Course.DoesNotExist:
            user.userprofile.courses.create(title=course)
    user.userprofile.save()
    scraper.driver.close()