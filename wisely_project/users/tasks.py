from __future__ import absolute_import, division
from datetime import datetime
import re
import time

from bs4 import BeautifulSoup
import dateutil.parser
from django.utils import timezone
import stripe
from pledges.models import Pledge
from users.coursera_scraping import CourseraDownloader
from users.edx_scraping import scrape_for_user

from users.models import Course, Quiz, Progress


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
            if self.driver.current_url != 'https://www.coursera.org/':
                return [], [], [], [], [], [], [], "Incorrect Login"
            soup = BeautifulSoup(self.driver.page_source)
            users_courses = soup.select(
                '#coursera-feed-tabs-current .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-name')
            info_links = soup.select(
                '#coursera-feed-tabs-current .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-links .internal-home')
            dates = soup.select(
                '#coursera-feed-tabs-current .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-progress .progress-label')
            start_dates = dates[::2]
            end_dates = dates[1::2]
            course_ids = soup.select('#coursera-feed-tabs-current .coursera-dashboard-course-listing-box')
            course_ids = map(lambda x: int(x.attrs['data-course-id']), course_ids)
            image_links = soup.select(
                '#coursera-feed-tabs-current .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-icon')
            image_links = map(lambda x: x.attrs['src'], image_links)
            return map(lambda x: x.contents[0].contents[0], users_courses), map(lambda x: x.contents[0].attrs['href'],
                                                                                users_courses), map(
                lambda x: x.attrs['href'],
                info_links), map(lambda x: str(x.contents[0] + ' 2014'), start_dates), map(
                lambda x: str(x.contents[0] + ' 2014'), end_dates), course_ids, image_links, None
        except:
            return [], [], [], [], [], [], [], None

    def get_upcoming_courses(self):
        try:
            soup = BeautifulSoup(self.driver.page_source)
            users_courses = soup.select(
                '#coursera-feed-tabs-future .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-name')
            info_links = soup.select(
                '#coursera-feed-tabs-future .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-links .internal-home')
            course_ids = soup.select('#coursera-feed-tabs-current .coursera-dashboard-course-listing-box')
            course_ids = map(lambda x: int(x.attrs['data-course-id']), course_ids)
            image_links = soup.select(
                '#coursera-feed-tabs-future .coursera-dashboard-course-listing-box .coursera-dashboard-course-listing-box-icon')
            image_links = map(lambda x: x.attrs['src'], image_links)
            return map(lambda x: x.contents[0].contents[0], users_courses), map(lambda x: x.contents[0].attrs['href'],
                                                                                users_courses), map(
                lambda x: x.attrs['href'],
                info_links), course_ids, image_links
        except:
            return [], [], [], [], []

    def get_quiz_link(self, course, link):
        if course.info_link:
            self.driver.get('https://www.coursera.org/' + course.info_link)
            soup = BeautifulSoup(self.driver.page_source)
            p_description = soup.select('.coursera-course-content p:first')
            if p_description:
                course.description = p_description[0].contents[0]
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
            course.quiz_link = link['href']
            self.driver.get(link['href'])
            soup = BeautifulSoup(self.driver.page_source)
            quiz_list = soup.select('div.course-item-list .course-item-list-header')
            quiz_details = soup.select('ul.course-item-list-section-list')
            for i, quiz_coursera in enumerate(quiz_list):
                heading = quiz_coursera.select('h3')[0].find(text=True, recursive=False)
                deadline = None
                try:
                    deadline = dateutil.parser.parse(str(
                        quiz_details[i].select('.course-quiz-item-softdeadline .course-assignment-deadline')[
                            0].contents[
                            0].replace('\n', '')))
                except IndexError:
                    pass
                hard_deadline = None
                try:
                    hard_deadline = dateutil.parser.parse(quiz_details[i].select(
                        '.course-quiz-item-harddeadline .course-assignment-deadline')[0].contents[
                                                              0].replace('\n', ''))
                except IndexError:
                    pass
                if hard_deadline is None:
                    hard_deadline = timezone.now()

                if deadline is None:
                    deadline = hard_deadline
                try:
                    Quiz.objects.get(heading=heading, course=course)
                except Quiz.DoesNotExist:
                    Quiz.objects.create(heading=heading,
                                        deadline=deadline,
                                        hard_deadline=hard_deadline,
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

    def get_course_completion(self, courseraprofile, pledges):
        self.driver.get('https://www.coursera.org/account/records')
        btn = self.driver.find_element_by_xpath(
            '//*[@id="origami"]/div/div/div[1]/div[3]/div[1]/div/div[2]/div[1]/div/a')
        if btn.is_displayed():
            btn.click()
            soup = BeautifulSoup(self.driver.page_source)
            course_ids = soup.select('.coursera-records-course-listing-box')
            course_ids = map(lambda x: int(x.attrs['data-course-id']), course_ids)
            grades = soup.select(
                '.coursera-course-records-listings-without .coursera-course-listing-grade-section div[class~=hide] span')[
                     ::2]
            for i, grade in enumerate(grades):
                if str(course_ids[i]) not in courseraprofile.counted_as_completed.split(','):
                    your_pledges = pledges.filter(course__course_id=course_ids[i])
                    for pledge in your_pledges:
                        mark = re.findall("\d+.\d+", grade.contents[0])
                        if mark:
                            pledge.actual_mark = float(mark[0]) / 100
                            pledge.is_complete = True
                            pledge.complete_date = timezone.now()
                            if pledge.is_active and pledge.charge != "":
                                if pledge.actual_mark > pledge.aim:
                                    charge = stripe.Charge.retrive(pledge.charge)
                                    charge.refund()
                            pledge.save()
                    if str(courseraprofile.counted_as_completed) != '':
                        courseraprofile.counted_as_completed += ',' + str(course_ids[i])
                    else:
                        courseraprofile.counted_as_completed += str(course_ids[i])

            courseraprofile.save()

    def end(self):
        self.driver.close()
        self.display.stop()


# def get_coursera_courses(profile):
#     scraper = CourseraScraper()
#     try:
#         if str(profile.username) != '':
#             print profile.username
#             scraper.driver.implicitly_wait(5)
#             scraper.login(str(profile.username), str(profile.password))
#             scraper.driver.set_page_load_timeout(3)
#             scraper.driver.set_script_timeout(5)
#             time.sleep(3)
#             courses, course_links, internal_links, start_dates, end_dates, course_ids, image_links, error = scraper.get_courses()
#             if error is not None:
#                 profile.incorrect_login = True
#                 profile.last_updated = timezone.now()
#                 profile.save()
#                 scraper.end()
#                 return
#             else:
#                 profile.incorrect_login = False
#             print courses, image_links
#             django_courses = []
#             try:
#                 for i, course in enumerate(courses):
#                     try:
#                         get_course = Course.objects.get(title=course)
#                         if get_course.start_date is None:
#                             get_course.course_link = course_links[i]
#                             get_course.info_link = internal_links[i]
#                             get_course.course_id = course_ids[i]
#                             get_course.image_link = image_links[i]
#                             get_course.start_date = datetime.strptime(
#                                 start_dates[i].replace('th', '').replace('st', '').replace('nd', '').replace('rd', ''),
#                                 "%b %d %Y").date()
#                             get_course.end_date = datetime.strptime(
#                                 end_dates[i].replace('th', '').replace('st', '').replace('nd', '').replace('rd', ''),
#                                 "%b %d %Y").date()
#                             get_course.save()
#                     except Course.DoesNotExist:
#                         get_course = Course.objects.create(title=course, course_link=course_links[i],
#                                                            course_id=course_ids[i],
#                                                            info_link=internal_links[i], start_date=
#                             datetime.strptime(
#                                 str(start_dates[i].replace('th', '').replace('st', '').replace('nd', '').replace('rd',
#                                                                                                                  '')),
#                                 '%b %d %Y').date(),
#                                                            end_date=datetime.strptime(str(
#                                                                end_dates[i].replace('th', '').replace('st', '').replace(
#                                                                    'nd',
#                                                                    '').replace(
#                                                                    'rd', '')), '%b %d %Y').date(),
#                                                            image_link=image_links[i])
#                     profile.courses.add(get_course)
#                     django_courses.append(get_course)
#             except IndexError:
#                 pass
#             except Exception as e:
#                 print e, "Inside"
#             f_courses, f_course_links, f_internal_links, f_course_ids, f_image_links = scraper.get_upcoming_courses()
#             print f_courses
#             try:
#                 for i, course in enumerate(f_courses):
#                     try:
#                         get_course = Course.objects.get(title=course)
#                     except Course.DoesNotExist:
#                         get_course = Course.objects.create(title=course, course_link=f_course_links[i],
#                                                            course_id=f_course_ids[i],
#                                                            image_link=f_image_links[i])
#                     profile.courses.add(get_course)
#             except IndexError:
#                 pass
#             except Exception as e:
#                 print e, "Inside"
#             profile.last_updated = timezone.now()
#             profile.save()
#             for i, course in enumerate(django_courses):
#                 get_course = course
#                 if get_course.end_date >= timezone.now().date():
#                     scraper.get_quiz_link(get_course, course_links[i])
#                     scraper.get_course_progress(profile.user, get_course)
#             scraper.get_course_completion(profile,
#                                           Pledge.objects.filter(user=profile.user.userprofile, is_complete=False))
#
#     except Exception as e:
#         print e
#     finally:
#         print "Coursera Done"
#         scraper.end()

def get_coursera_courses(profile):
    try:
        coursera = CourseraDownloader(profile.username, profile.password)
        coursera.login('gamification-003', profile)
        coursera.get_enrollments(profile)
    except Exception as e:
        print e


def get_edx_courses(edxprofile):
    if edxprofile.email != '':
        scrape_for_user(edxprofile)
    else:
        return
